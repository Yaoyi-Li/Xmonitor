import json
import platform
import psutil
import os
import time
import heapq
from py3nvml import py3nvml as N




def bytes2GB(n):
    prefix = 1 << 3 * 10
    value = round((float(n) / prefix)*10)/10
    return value

def bytes2human(n):
    symbols = ('K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y')
    prefix = {}
    for i, s in enumerate(symbols):
        prefix[s] = 1 << (i + 1) * 10
    for s in reversed(symbols):
        if n >= prefix[s]:
            value = float(n) / prefix[s]
            return '%.1f%s' % (value, s)
    return "%dB" % n



class SysinfoCollector():
    
    _TOP_CPU_NUM = 10
    _TOP_MEM_NUM = 10
    _SUBUID_PATH = '/etc/subuid'

    def __init__(self, require = [ 'CPU' ]):

        self._require = require
        self.hostname = platform.node()
        self.dist, self.dist_version, _ = platform.linux_distribution()
        self.jsonObj = { 
            'HOSTNAME': self.hostname,
            'DIST': self.dist,
            'VERSION': self.dist_version
        }
        self._timeLast = 0
        self._netSentLast = 0
        self._netRecvLast = 0
        self._procInfo = None

        self._impulse = 0
        self._memProcessObj = {}
        self._cpuProcessObj = {}
        self._ioProcessObj = {}
        self._gpuInfoObj = {}

        self._subuidCache = {}
        self._subuidDict = self._loadSubuid(self._SUBUID_PATH)
        

    def getCpuInfo(self):
        cpuInfoObj = {}

        cpuCount = psutil.cpu_count()
        cpuInfoObj['CPU_COUNT'] = cpuCount

        cpuPercents = psutil.cpu_times_percent(interval=None, percpu=True)
        cpuPercentsObj = {}
        for cpuCnt, singleCpu in enumerate(cpuPercents):
            cpuUser = singleCpu.user
            cpuSystem = singleCpu.system
            cpuIO = singleCpu.iowait
            cpuIdle = singleCpu.idle
            cpuOther = 100 - cpuUser - cpuSystem - cpuIdle - cpuIO
            cpuOther = round(cpuOther*10)/10 if cpuOther>0 else 0.0
            cpuPercentsObj[cpuCnt] = {
                'USER': cpuUser,
                'SYSTEM': cpuSystem,
                'IO': cpuIO,
                'OTHER': cpuOther,
                'IDLE': cpuIdle
            }
        cpuInfoObj['CPU_PERCENT'] = cpuPercentsObj

        return cpuInfoObj


    def getMemInfo(self):

        mem = psutil.virtual_memory()
        memTotal = mem.total
        memAvailable = mem.available
        memFree = mem.free
        memUsed = memTotal - memAvailable
        memCached = memTotal - memFree - memUsed
        memPercent = mem.percent
        memInfoObj = {
            'TOTAL': bytes2GB(memTotal),
            'USED': bytes2GB(memUsed),
            'CACHED': bytes2GB(memCached),
            'PERCENT': memPercent
        }

        return memInfoObj


    def getNetInfo(self):
        net = psutil.net_io_counters()
        netSent = net.bytes_sent
        netRecv = net.bytes_recv

        if self._netRecvLast == 0:
            netRecvSpeed = 0
        else:
            netRecvSpeed = (netRecv - self._netRecvLast) / (self._timeNow - self._timeLast)
        
        if self._netSentLast == 0:
            netSentSpeed = 0
        else:
            netSentSpeed = (netSent - self._netSentLast) / (self._timeNow - self._timeLast)

        netObj = {
            'RECV': round(netRecvSpeed),
            'SENT': round(netSentSpeed),
            'RECV_STR': bytes2human(netRecvSpeed)+'/s',
            'SENT_STR': bytes2human(netSentSpeed)+'/s'
        }

        self._netRecvLast = netRecv
        self._netSentLast = netSent


        return netObj


    def getSwapInfo(self):
        swap = psutil.swap_memory()
        swapTotal = swap.total
        swapUsed = swap.used
        swapPercent = swap.percent
        swapInfoObj = {
            'TOTAL': bytes2GB(swapTotal),
            'USED': bytes2GB(swapUsed),
            'PERCENT': bytes2GB(swapPercent)
        }

        return swapInfoObj


    def getMemProcessInfo(self):
        if (self._impulse % 3) != 0:
            return self._memProcessObj

        try:
            memProcInfo = psutil.process_iter(attrs=['name', 'username', 'memory_info'])
        except:
            pass

        # memProcInfoSorted = sorted(memProcInfo, key=lambda p: p.info['memory_info'])
        # memProcInfoTop = memProcInfoSorted[:-self._TOP_MEM_NUM-1:-1]
        memProcInfoTop = heapq.nlargest(self._TOP_MEM_NUM, memProcInfo, key=lambda p: p.info['memory_info'].rss)

        memProcessObj = {
            'TOP': self._TOP_MEM_NUM
        }
        for cnt, process in enumerate( memProcInfoTop):
            memProcessObj[str(cnt)] = {
                'NAME': process.info['name'],
                'PID': process.pid,
                'USERNAME': self._getSubuidName(process.info['username']),
                'MEM': bytes2human(process.info['memory_info'].rss)
            }

        self._memProcessObj = memProcessObj

        return memProcessObj

    def getCpuProcessInfo(self):
        if (self._impulse % 3) != 0:
            return self._cpuProcessObj

        try:
            cpuProcInfo = psutil.process_iter(attrs=['name', 'username', 'cpu_percent'])
        except:
            pass

        # cpuProcInfoSorted = sorted(cpuProcInfo, key=lambda p: p.info['cpu_percent'])
        # cpuProcInfoTop = cpuProcInfoSorted[:-self._TOP_CPU_NUM-1:-1]
        cpuProcInfoTop = heapq.nlargest(self._TOP_CPU_NUM, cpuProcInfo, key=lambda p: p.info['cpu_percent'])

        cpuProcessObj = {
            'TOP': self._TOP_CPU_NUM
        }
        for cnt, process in enumerate(cpuProcInfoTop):
            cpuProcessObj[str(cnt)] = {
                'NAME': process.info['name'],
                'PID': process.pid,
                'USERNAME': self._getSubuidName(process.info['username']),
                'CPU': str(process.info['cpu_percent']) + '%'
            }
        
        self._cpuProcessObj = cpuProcessObj

        return cpuProcessObj


    def getIoProcessInfo(self):
        if self._impulse != 0:
            return self._ioProcessObj

        try:
            ioProcInfo = psutil.process_iter(attrs=['name', 'username', 'io_counters'])
        except:
            pass

        # ioProcInfoSorted = sorted(ioProcInfo, key=lambda p: 0 if not p.info['io_counters'] else \
                            # p.info['io_counters'].write_bytes + p.info['io_counters'].read_bytes)
        # ioProcInfoTop = ioProcInfoSorted[:-self._TOP_CPU_NUM-1:-1]

        ioProcInfoTop = heapq.nlargest(self._TOP_CPU_NUM, ioProcInfo, key=lambda p: 0 if not \
                        p.info['io_counters'] else p.info['io_counters'].write_bytes + p.info['io_counters'].read_bytes)

        ioProcessObj = {
            'TOP': self._TOP_CPU_NUM
        }
        for cnt, process in enumerate(ioProcInfoTop):
            ioProcessObj[str(cnt)] = {
                'NAME': process.info['name'],
                'PID': process.pid,
                'USERNAME': self._getSubuidName(process.info['username']),
                'READ': bytes2human(process.info['io_counters'].read_bytes),
                'WRITE': bytes2human(process.info['io_counters'].write_bytes)
            }

        self._ioProcessObj = ioProcessObj
        
        return ioProcessObj



    def getGpuInfo(self):
        if (self._impulse % 2) != 0:
            return self._gpuInfoObj

        try:
            N.nvmlInit()
            gpuInfoObj = {}

            driverVersion = N.nvmlSystemGetDriverVersion()
            deviceCnt = N.nvmlDeviceGetCount()

            gpuInfoObj['DRIVER_VERSION'] = driverVersion
            gpuInfoObj['DEVICE_COUNT'] = deviceCnt

            for dCnt in range(deviceCnt):
                deviceInfoObj = {}
                handle = N.nvmlDeviceGetHandleByIndex(dCnt)
                name = N.nvmlDeviceGetName(handle)

                try:
                    fan = N.nvmlDeviceGetFanSpeed(handle)
                except N.NVMLError as err:
                    fan = 'N/A'

                try:
                    temp = N.nvmlDeviceGetTemperature(handle, N.NVML_TEMPERATURE_GPU)
                except N.NVMLError as err:
                    temp = 'N/A'

                try:
                    powerUsage = round(N.nvmlDeviceGetPowerUsage(handle) / 1000)
                except N.NVMLError as err:
                    powerUsage = 'N/A'

                try:
                    powerLimit = round(N.nvmlDeviceGetPowerManagementLimit(handle) / 1000)
                except N.NVMLError as err:
                    powerLimit = 'N/A'

                try:
                    memInfo = N.nvmlDeviceGetMemoryInfo(handle)
                    memUsage = round(memInfo.used/1024/1024)
                    memTotal = round(memInfo.total/1024/1024)
                except N.NVMLError as err:
                    memUsage = 'N/A'
                    memTotal = 'N/A'

                try:
                    util = N.nvmlDeviceGetUtilizationRates(handle).gpu
                except N.NVMLError as err:
                    util = 'N/A'

                deviceInfoObj['NAME'] = name
                deviceInfoObj['FAN'] = fan
                deviceInfoObj['TEMP'] = temp
                deviceInfoObj['POWER_USAGE'] = powerUsage
                deviceInfoObj['POWER_LIMIT'] = powerLimit
                deviceInfoObj['MEM_USAGE'] = memUsage
                deviceInfoObj['MEM_TOTAL'] = memTotal
                deviceInfoObj['UTIL'] = util

                gpuProcessObj = {}
                try:
                    processes = N.nvmlDeviceGetComputeRunningProcesses(handle)
                except N.NVMLError as err:
                    processes = []
                for pCnt, process in enumerate(processes):
                    gpuMem = round(process.usedGpuMemory / 1024 / 1024)
                    pid = process.pid

                    try:
                        p = psutil.Process(pid)
                        attrs = p.as_dict(attrs = ['name', 'username', 'status'])
                    except psutil.ZombieProcess:
                        attrs = {'name': 'unknown', 'username': 'unknown', 'status': 'zombie'}
                    except:
                        pass
                    
                    gpuProcessObj[str(pCnt)] = {
                        'PID': pid,
                        'MEM': gpuMem,
                        'NAME': attrs['name'],
                        'USERNAME': self._getSubuidName(attrs['username']),
                        'STATUS': attrs['status']
                    }

                deviceInfoObj['PROCESS'] = gpuProcessObj
                gpuInfoObj[str(dCnt)] = deviceInfoObj

            N.nvmlShutdown()

        except N.NVMLError as err:
            N.nvmlShutdown()
            print(err)
            gpuInfoObj = {}

        self._gpuInfoObj = gpuInfoObj
        return gpuInfoObj


    def sysinfo2Obj(self):
        self._timeNow = time.time()
        self.jsonObj['TIME'] = round(self._timeNow)

        for item in self._require:
            self.jsonObj[item] = self._FUNC_TABLE[item](self)


        self._impulse = (self._impulse + 1) % 6
        self._timeLast = self._timeNow
        return self.jsonObj


    def sysinfo2JSON(self):        
        data = self.sysinfo2Obj()

        try:
            serialized = json.dumps(data)
        except (TypeError, ValueError) as e:
            raise Exception('Not JSON-serializable data')
        return serialized
    

    def __str__(self):
        return json.dumps(self.sysinfo2Obj(), indent=4, separators=(',', ':'))


    def _getSubuidName(self, username):
        if username.isdigit():
            subuid = int(username)
            if subuid in self._subuidCache:
                name = self._subuidCache[subuid]
            else:
                name = 'unknown'
                # _subuidDict: {subuid_start: [username, subuid_interval]}
                for key, value in self._subuidDict.items():
                    if subuid >= key and (subuid - key) < value[1]:
                        name = value[0]
                self._subuidCache[subuid] = name
        else:
            name = username
        
        return name


    def _loadSubuid(self, path):
        subuidDict = {}
        if os.path.isfile(path):
            try:
                with open(path, 'r') as f:
                    buf = f.readline()
                    while buf:
                        splitBuf = buf.strip().split(':')
                        subuidDict[int(splitBuf[1])] = [splitBuf[0], int(splitBuf[2])]
                        buf = f.readline()
            except:
                subuidDict = {}
        
        return subuidDict
            
            

    _FUNC_TABLE = {
        'CPU': getCpuInfo,
        'MEM': getMemInfo,
        'NET': getNetInfo,
        'SWAP': getSwapInfo,
        'GPU': getGpuInfo,
        'CPU_PROCESS': getCpuProcessInfo,
        'MEM_PROCESS': getMemProcessInfo,
        'IO_PROCESS': getIoProcessInfo,
    }



if __name__ == '__main__':

    REQUIRE = [
        'CPU',
        'MEM',
        'NET',
        'SWAP',
        'GPU',
        'MEM_PROCESS',
        'CPU_PROCESS',
        'IO_PROCESS',
    ]

    sysinfo = SysinfoCollector(REQUIRE)
    print(sysinfo)
    time.sleep(0.5)
    print(sysinfo)
    time.sleep(0.5)
    print(sysinfo)
    time.sleep(0.5)
    print(sysinfo)
    # for i in range(10):
    #     sysinfo.sysinfo2Obj()