#!/usr/bin/env python3
"""Fail-closed, supervised BSC N1 Windows one-shot WH3 native source probe.

This does not modify game data. Frida installs temporary code hooks, explicitly
removed by the agent before shutdown. The parent supervises a short-lived
worker because older Frida detach operations can block on the user's system.
"""
import argparse
import ctypes
from ctypes import wintypes
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import threading
import time

SHA = '518c4f292f275142df13b96b9db704a3db7b4870b2c519df83d850596ecc822a'
PROBE = Path(__file__).with_name('one_shot_native_source.js')


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(8 << 20), b''):
            digest.update(chunk)
    return digest.hexdigest()


def query_pid_image(pid: int) -> Path:
    """Query process executable pathname without trusting process titles alone."""
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD,
                                                 wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
    kernel.QueryFullProcessImageNameW.restype = wintypes.BOOL
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.CloseHandle.restype = wintypes.BOOL
    handle = kernel.OpenProcess(0x1000, False, pid)
    if not handle:
        raise ValueError('CANNOT_QUERY_PID_' + str(pid))
    try:
        buffer = ctypes.create_unicode_buffer(32768)
        limit = wintypes.DWORD(len(buffer))
        if not kernel.QueryFullProcessImageNameW(handle, 0, buffer, ctypes.byref(limit)):
            raise ValueError('PID_EXECUTABLE_PATH_QUERY_FAILED')
        return Path(buffer.value).resolve(strict=True)
    finally:
        kernel.CloseHandle(handle)


def validate(exe: Path, pid: int, output: Path) -> Path:
    """Verify version first, then OS/PID path and SHA (fail closed)."""
    exe = exe.resolve(strict=True)
    output = output.resolve()
    if exe == output:
        raise ValueError('REFUSE_TO_OVERWRITE_GAME_EXE')
    if sha256(exe) != SHA:
        raise ValueError('GAME_SHA256_MISMATCH')
    if platform.system() != 'Windows' or platform.architecture()[0] != '64bit':
        raise ValueError('WINDOWS_64BIT_ONLY')
    observed = query_pid_image(pid)
    if os.path.normcase(str(exe)) != os.path.normcase(str(observed)):
        raise ValueError('PID_EXE_PATH_MISMATCH:' + str(observed))
    if sha256(observed) != SHA:
        raise ValueError('PID_GAME_VERSION_CHANGED')
    if not PROBE.exists():
        raise ValueError('PROBE_JS_MISSING')
    return exe


def worker(exe: Path, pid: int, out: Path, seconds: int) -> int:
    validate(exe, pid, out)
    try:
        import frida
    except ImportError as exc:
        raise ValueError('FRIDA_MISSING_USE_PYTHON_MINUS_M_PIP_INSTALL_FRIDA') from exc

    ready = threading.Event()
    stopped = threading.Event()
    error = []
    seen = 0
    session = None
    script = None
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open('w', encoding='utf-8') as stream:
        def on_message(message, binary):
            nonlocal seen
            if message.get('type') == 'send':
                item = message.get('payload')
                if not isinstance(item, dict):
                    item = {'type': 'bad_payload', 'repr': repr(item)}
                if item.get('type') == 'ready':
                    ready.set()
                elif item.get('type') == 'summary':
                    stopped.set()
            else:
                item = {'type': 'probe_error', 'error': message}
                error.append(str(message)[:1600])
                ready.set()
                stopped.set()
            seen += 1
            stream.write(json.dumps(item, ensure_ascii=False) + '\n')
            stream.flush()

        try:
            session = frida.attach(pid)
            script = session.create_script(PROBE.read_text(encoding='utf-8'))
            script.on('message', on_message)
            script.load()
            if not ready.wait(timeout=7):
                raise RuntimeError('PROBE_READY_TIMEOUT')
            if error:
                raise RuntimeError('PROBE_SETUP_ERROR:' + error[0])
            print('TRACE_ACTIVE: native source capture enabled for ' + str(seconds) + ' seconds', flush=True)
            time.sleep(seconds)
        finally:
            if script is not None:
                try:
                    script.post({'type': 'stop'})
                    if not stopped.wait(timeout=3):
                        print('WARN: JS stop acknowledgement missing; process should be closed after review',
                              flush=True)
                except Exception as exc:
                    print('WARN: JS stop failed: ' + str(exc), flush=True)
            if session is not None:
                # Do not let native Frida detach stall the worker forever.
                detach_thread = threading.Thread(target=session.detach, daemon=True)
                detach_thread.start()
                detach_thread.join(timeout=1.5)
                if detach_thread.is_alive():
                    print('WARN: Frida native detach slow; parent watchdog will ensure Python exits',
                          flush=True)
        print('TRACE_SAVED: ' + str(out) + ' events=' + str(seen), flush=True)
    if error:
        raise RuntimeError('PROBE_ERROR:' + error[0])
    if not stopped.is_set():
        raise RuntimeError('NO_AGENT_STOP_CONFIRMATION')
    return 0


def parent(exe: Path, pid: int, out: Path, seconds: int) -> int:
    validate(exe, pid, out)
    command = [sys.executable, str(Path(__file__).resolve()), '--worker',
               '--exe', str(exe), '--pid', str(pid), '--out', str(out),
               '--seconds', str(seconds)]
    print('TRACE_STARTING: guarded original SHA and exact PID matched.', flush=True)
    proc = subprocess.Popen(command)
    try:
        return_code = proc.wait(timeout=seconds + 15)
    except subprocess.TimeoutExpired:
        print('FAIL_CLOSED: Worker stuck in native cleanup; terminating Python worker (not game).',
              flush=True)
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=3)
        return_code = 5
    except KeyboardInterrupt:
        print('STOP_REQUESTED: terminating worker; captured JSONL may still be usable.', flush=True)
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()
        return 130
    try:
        lines = out.read_text(encoding='utf-8-sig').splitlines()
        records = [json.loads(row) for row in lines if row.strip()]
    except (OSError, ValueError) as exc:
        print('TRACE_INVALID_OR_MISSING_JSONL:' + str(exc), flush=True)
        return return_code if return_code != 0 else 7
    summaries=[x for x in records if x.get('type')=='summary']
    if not summaries:
        print('TRACE_NO_SUMMARY: Capture may be incomplete; retain JSONL.', flush=True)
        return return_code if return_code != 0 else 7
    if any(x.get('type') in ('probe_error','bad_payload') for x in records):
        print('TRACE_AGENT_ERRORS: raw JSONL saved, do not repeat the test.', flush=True)
        return return_code if return_code != 0 else 7
    if summaries[-1].get('detachErrors'):
        print('TRACE_AGENT_UNHOOK_ERROR: preserve trace; no automatic retest.', flush=True)
        return return_code if return_code != 0 else 7
    if return_code != 0:
        # The native Frida Python-side detach MAY block after the JS agent has
        # already detached all hooks and emitted its acknowledgement. Preserve
        # the complete capture rather than falsely reporting no test data.
        print('WARN_PYTHON_WORKER_EXIT_STALLED: complete JS summary was saved; '
              'the collector was supervised/killed, not the game.', flush=True)
    print('TRACE_FINISHED: ' + str(out) + ' (' + str(len(records)) + ' records)', flush=True)
    try:
        from analyze_one_shot import analyze
        analyzed=analyze(records)
        report_path=out.with_name(out.stem+'_report.json')
        report_path.write_text(json.dumps(analyzed,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
        print('TRACE_ANALYSIS: '+analyzed['grade'],flush=True)
        print('REPORT_SAVED: '+str(report_path),flush=True)
    except Exception as exc:
        print('ANALYSIS_FAILED_BUT_TRACE_SAVED:'+str(exc),flush=True)
        return 8
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--exe', required=True, type=Path)
    ap.add_argument('--pid', required=True, type=int)
    ap.add_argument('--seconds', default=18, type=int)
    ap.add_argument('--out', default=Path('bsc_once_source.jsonl'), type=Path)
    ap.add_argument('--worker', action='store_true', help=argparse.SUPPRESS)
    args = ap.parse_args(argv)
    if not 5 <= args.seconds <= 60:
        ap.error('Seconds must be in [5, 60]')
    if not 1 <= args.pid <= 2**32-1:
        ap.error('INVALID_PID')
    try:
        if args.worker:
            return worker(args.exe, args.pid, args.out, args.seconds)
        return parent(args.exe, args.pid, args.out, args.seconds)
    except (ValueError, RuntimeError, OSError) as exc:
        print('FAIL_CLOSED:' + str(exc), file=sys.stderr, flush=True)
        return 2


if __name__ == '__main__':
    sys.exit(main())
