#pragma once
#include <cstddef>
// Bind the WH3 float32 Lua 5.1 ABI dynamically. No bundled second Lua VM.
struct lua_State;
namespace wh3::lua51 {
using Number=float;
using CFunction=int (*)(lua_State*);
struct Api {
    void (*settop)(lua_State*,int)=nullptr;
    void (*pushvalue)(lua_State*,int)=nullptr;
    int (*pcall)(lua_State*,int,int,int)=nullptr;
    int (*gettop)(lua_State*)=nullptr;
    int (*type)(lua_State*,int)=nullptr;
    const char* (*tolstring)(lua_State*,int,std::size_t*)=nullptr;
    Number (*tonumber)(lua_State*,int)=nullptr;
    int (*toboolean)(lua_State*,int)=nullptr;
    void* (*touserdata)(lua_State*,int)=nullptr;
    void (*pushnil)(lua_State*)=nullptr;
    void (*pushnumber)(lua_State*,Number)=nullptr;
    void (*pushlstring)(lua_State*,const char*,std::size_t)=nullptr;
    void (*pushboolean)(lua_State*,int)=nullptr;
    void (*createtable)(lua_State*,int,int)=nullptr;
    void (*setfield)(lua_State*,int,const char*)=nullptr;
    void (*rawseti)(lua_State*,int,int)=nullptr;
    void (*pushcclosure)(lua_State*,CFunction,int)=nullptr;
};
Api& api();
bool bind();
int open(lua_State*);
} // namespace wh3::lua51
