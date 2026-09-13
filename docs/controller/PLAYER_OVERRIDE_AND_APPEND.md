# Player Override and Shift Append

## Append

Queued external action extends the active shadow timeline at any stage: before takeover, during Move tracking, during Attack approach/hold, or after the currently known tail.

## Replace

Ordinary non-Shift RMB is replacement authority. The old generation is cancelled immediately. No stale scripted action or late ACK may revive the old pN.

## Revision races

A queued append may change native revision while a Controller issue is pending. HF5 handles append-only stale redecision separately from true player replacement; it does not simply reuse an old decision with the newest revision.
