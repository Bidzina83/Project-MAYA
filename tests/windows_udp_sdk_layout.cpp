#include <winsock2.h>
#include <ws2tcpip.h>
#include <windows.h>
#include <iphlpapi.h>
#include <fwpmu.h>
#include <stddef.h>
static_assert(sizeof(void*) == 8, "x64 only");
static_assert(sizeof(FWPM_NET_EVENT_HEADER3) == 136, "header");
static_assert(sizeof(FWPM_NET_EVENT5) == 152, "event");
static_assert(offsetof(FWPM_NET_EVENT5, classifyDrop) == 144, "event union");
static_assert(offsetof(FWPM_NET_EVENT_HEADER3, packageSid) == 96, "package");
static_assert(offsetof(FWPM_NET_EVENT_HEADER3, appId) == 64, "app");
static_assert(offsetof(FWPM_NET_EVENT_HEADER3, localPort) == 52, "port");
static_assert(offsetof(FWPM_NET_EVENT_CLASSIFY_DROP2, msFwpDirection) == 24, "direction");
static_assert(offsetof(FWPM_NET_EVENT_CLASSIFY_DROP2, vSwitchId) == 32, "switch");
static_assert(offsetof(FWPM_LAYER0, layerId) == 64, "layer id");
static_assert(offsetof(FWP_VALUE0, uint32) == 8, "option value");
static_assert(sizeof(MIB_UDPROW_OWNER_PID) == 12, "IPv4 owner row");
static_assert(offsetof(MIB_UDPTABLE_OWNER_PID, table) == 4, "IPv4 owner table");
static_assert(sizeof(MIB_UDP6ROW_OWNER_PID) == 28, "IPv6 owner row");
static_assert(offsetof(MIB_UDP6TABLE_OWNER_PID, table) == 4, "IPv6 owner table");
static_assert(offsetof(MIB_UDP6ROW_OWNER_PID, dwLocalPort) == 20, "IPv6 port");
static_assert(offsetof(MIB_UDP6ROW_OWNER_PID, dwOwningPid) == 24, "IPv6 PID");
