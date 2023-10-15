from renderer.data import ReplayData, Events
from interpolation.interpolator.liner import LinerInterpolationer
import math
import copy
import logging
import collections
from tqdm import tqdm

class Interpolator():
    def interpolate(self, 
            replay_info: ReplayData,
            fpsTarget=60,
            speedScale=6.0,
            method="liner"
            ):
        logging.info("started interpolating")
        # add more frames in replays to support higher fps
        # by default, one frame in game represents 1 second
        origTotLen=len(replay_info.events)
        # number of events in one sec
        evtsPerSec=fpsTarget/speedScale 

        # total events 
        afterLen=int((origTotLen - 1)/evtsPerSec) + 1   

        newRepInfo=[]
        for i in tqdm(range(origTotLen)):
            currentLenTarget=evtsPerSec*(i+1)
            # in case speed scale is faster than 60 events per sec
            if currentLenTarget <= len(newRepInfo):
                continue
            
            originEvt=replay_info.events[i+2]
            newRepInfo.append(originEvt)
            if originEvt.last_frame :
                break
            nextEvt=replay_info.events[i+3] 

            eventsToAdd=math.floor(currentLenTarget - len(newRepInfo)) - 1

            match method:
                case "liner":
                    # liner implementation
                    for item in (LinerInterpolationer().doLinerInterpolation(originEvt, nextEvt, eventsToAdd)):
                        newRepInfo.append(item)
                case "bezier":
                    # todo
                    raise NotImplementedError("not implemented")
        logging.info("interpolation complete")  
        tmp = replay_info._asdict()
        tmp['events']=dict(zip(range(len(newRepInfo)), newRepInfo))
        return toNamedTuple('ReplayData', tmp)
    
def toNamedTuple(name: str, evt: dict):
        keyList=evt.keys()
        valueList=evt.values()
        tmpTuple=collections.namedtuple(name, keyList)
        return tmpTuple._make(valueList)

    