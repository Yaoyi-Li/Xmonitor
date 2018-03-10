import json
import platform
import psutil
import time


def bytes2GB(n):
    prefix = 1 << 3 * 10
    value = round((float(n) / prefix)*10)/10
    return value

def bytes2human(n):
    # http://code.activestate.com/recipes/578019
    # >>> bytes2human(10000)
    # '9.8K'
    # >>> bytes2human(100001221)
    # '95.4M'
    symbols = ('K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y')
    prefix = {}
    for i, s in enumerate(symbols):
        prefix[s] = 1 << (i + 1) * 10
    for s in reversed(symbols):
        if n >= prefix[s]:
            value = float(n) / prefix[s]
            return '%.1f%s' % (value, s)
    return "%sB" % n

class SysinfoCollector():

    def __init__(self, require = [ 'CPU' ]):

        self._require = require
        self.hostname = platform.node()
        self.dist, self.dist_version, _ = platform.linux_distribution()
        self.jsonObj = { 
            'HOSTNAME': self.hostname,
            'DIST': self.dist,
            'VERSION': self.dist_version
        }
        

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


    def sysinfo2Obj(self):
        self.jsonObj['TIME'] = round(time.time())

        for item in self._require:
            self.jsonObj[item] = self.FUNC_TABLE[item](self)
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


    FUNC_TABLE = {
        'CPU': getCpuInfo,
        'MEM': getMemInfo
    }



if __name__ == '__main__':

    REQUIRE = [
        'CPU',
        'MEM'
    ]

    sysinfo = SysinfoCollector(REQUIRE)
    print(sysinfo)
    time.sleep(0.3)
    print(sysinfo)