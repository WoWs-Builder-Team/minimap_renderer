from typing import NamedTuple, Optional
from renderer.data import (
    PlayerInfo,
    Vehicle,
    ReplayData,
    Events,
    Smoke,
    Shot,
    Torpedo,
    Consumable,
    Plane,
    Ward,
    ControlPoint,
    Score,
    Frag,
    Message,
    BattleResult,
    BuildingInfo,
    Building,
    Units,
    Skills,
    AcousticTorpedo,
)
import math
import copy
import logging
import collections
      
class VehicleDiff(NamedTuple):
    x: float
    y: float
    yaw: float
    regenerated_health: float
    regen_crew_hp_limit: float
    regeneration_health: float
    
class PlaneDiff(NamedTuple):
    x: float
    y: float

class ShotDiff(NamedTuple):
    origX: float
    origY: float
    destX: float
    destY: float

class TorpedoDiff(NamedTuple):
    x: float
    y: float
    yaw: float

class AcousticTorpedoDiff(NamedTuple):
    x: float
    y: float
    yaw: float      

# dict key is id of elements（vehicle_id, plane_id, etc.).
class LinerDiff(NamedTuple):
       vehicleDiff: dict[int, VehicleDiff]
       planeDiff: dict[int, PlaneDiff]
       shotDiff: dict[int, ShotDiff]
       torpedoDiff: dict[int, TorpedoDiff]
       acousticTorpedoDiff: dict[int, AcousticTorpedoDiff]

class LinerInterpolationer:
   
    def __init__(self) -> None:
        pass
          
    def doLinerInterpolation(self, originEvt: Events, nextEvt: Events, eventsToAdd: int):
        result = []
        if eventsToAdd <= 0 :
            return result
        diffData=self.calcDiff(originEvt, nextEvt, eventsToAdd)
        currentEvt = self.initCurrentEvt(originEvt)
        for i in range(eventsToAdd): 
            tmpEvt = currentEvt._asdict()
            self.applyDiffData(diffData, tmpEvt)
            currentEvt = toNamedTuple('Events', tmpEvt)
            result.append(currentEvt)
        return result

    def initCurrentEvt(self, originEvt: Events):
        currentEvt = Events(
            time_left=originEvt.time_left,
            evt_vehicle=originEvt.evt_vehicle,
            evt_plane=originEvt.evt_plane,
            evt_shot=[],
            evt_torpedo=originEvt.evt_torpedo,
            evt_acoustic_torpedo=originEvt.evt_acoustic_torpedo,
            evt_building = dict(),
            evt_ward = originEvt.evt_ward,
            evt_smoke = originEvt.evt_smoke,
            evt_hits = [],
            evt_consumable = dict(),
            evt_control = originEvt.evt_control,
            evt_score = originEvt.evt_score,
            evt_damage_maps = originEvt.evt_damage_maps,
            evt_frag = [],
            evt_ribbon = dict(),
            evt_achievement = dict(),
            evt_times_to_win = originEvt.evt_times_to_win,
            evt_chat = [],
        )
        return currentEvt
    
    def calcDiff(self, originEvt: Events, nextEvt: Events, eventsToAdd: int):
        result=LinerDiff(
            vehicleDiff=self.calcVehicle(originEvt, nextEvt, eventsToAdd),
            planeDiff=self.calcPlaneDiff(originEvt, nextEvt, eventsToAdd),
            shotDiff=self.calcShotDiff(originEvt, nextEvt, eventsToAdd),
            torpedoDiff=self.calcTorpedoDiff(originEvt, nextEvt, eventsToAdd),
            acousticTorpedoDiff=self.calcAcousticTorpedoDiff(originEvt, nextEvt, eventsToAdd)
        )
        return result
    
    def calcVehicle(self, originEvt: Events, nextEvt: Events, eventsToAdd: int):
        result=dict()
        if eventsToAdd <= 0:
            return result
        for id, vehicle in originEvt.evt_vehicle.items():
            nextVehicle=nextEvt.evt_vehicle.get(id)
            if nextVehicle == None: 
                continue
            result[id]=VehicleDiff(
                float(nextVehicle.x - vehicle.x)/ float(eventsToAdd),
                float(nextVehicle.y - vehicle.y)/ float(eventsToAdd),
                (nextVehicle.yaw - vehicle.yaw )/ eventsToAdd,
                (nextVehicle.regenerated_health - vehicle.regenerated_health)/ eventsToAdd,
                (nextVehicle.regen_crew_hp_limit - vehicle.regen_crew_hp_limit)/ eventsToAdd,
                (nextVehicle.regeneration_health - vehicle.regeneration_health)/ eventsToAdd
            )

        return result

    def calcPlaneDiff(self, originEvt: Events, nextEvt: Events, eventsToAdd: int):
        result=dict()
        if eventsToAdd <= 0:
            return result
        for id, plane in originEvt.evt_plane.items():
            nextPlane=nextEvt.evt_plane.get(id)
            if nextPlane == None: 
                continue
            result[id]=PlaneDiff(
                float(nextPlane.position[0] - plane.position[0])/ float(eventsToAdd),
                float(nextPlane.position[1] - plane.position[1])/ float(eventsToAdd)
            )

        return result

    def calcShotDiff(self, originEvt: Events, nextEvt: Events, eventsToAdd: int):
        result=dict()
        if eventsToAdd <= 0:
            return result
        for shot in originEvt.evt_shot:
            id=shot.shot_id
            
            nextShot=None
            for tmp in nextEvt.evt_shot:
                if tmp.shot_id==id:
                    nextShot=tmp
                    break
            if nextShot == None: 
                continue
            result[id]=ShotDiff(
                float(nextShot.origin[0] - shot.origin[0])/ float(eventsToAdd),
                float(nextShot.origin[1] - shot.origin[1])/ float(eventsToAdd),
                float(nextShot.destination[0] - shot.destination[0])/ float(eventsToAdd),
                float(nextShot.destination[1] - shot.destination[1])/ float(eventsToAdd),
            )

        return result

    def calcTorpedoDiff(self, originEvt: Events, nextEvt: Events, eventsToAdd: int):
        result=dict()
        if eventsToAdd <= 0:
            return result
        for id, torpedo in originEvt.evt_torpedo.items():
            nextTorpedo=nextEvt.evt_torpedo.get(id)
            if nextTorpedo == None: 
                continue
            result[id]=TorpedoDiff(
                float(nextTorpedo.x - torpedo.x)/ float(eventsToAdd),
                float(nextTorpedo.y - torpedo.y)/ float(eventsToAdd),
                (nextTorpedo.yaw - torpedo.yaw )/ eventsToAdd,
           )

        return result

    def calcAcousticTorpedoDiff(self, originEvt: Events, nextEvt: Events, eventsToAdd: int):
        result=dict()
        if eventsToAdd <= 0:
            return result
        for id, acousticTorpedo in originEvt.evt_acoustic_torpedo.items():
            nextAcousticTorpedo=nextEvt.evt_acoustic_torpedo.get(id)
            if nextAcousticTorpedo == None: 
                continue
            result[id]=TorpedoDiff(
                float(nextAcousticTorpedo.x - acousticTorpedo.x)/ float(eventsToAdd),
                float(nextAcousticTorpedo.y - acousticTorpedo.y)/ float(eventsToAdd),
                (nextAcousticTorpedo.yaw - acousticTorpedo.yaw )/ eventsToAdd,
           )

        return result


    def applyDiffData(self, diffData: LinerDiff, currentEvt: dict):
        tmp=[]
        for id, vehicle in currentEvt['evt_vehicle'].items():
            vehicle: Vehicle
            diffVehicle = diffData.vehicleDiff.get(id)
            diffVehicle: VehicleDiff

            if diffVehicle == None:
                logging.debug("diffVehicle: id %s is none.", vehicle.vehicle_id)
                continue
            dic = vehicle._asdict()
            dic['x']=dic['x'] + diffVehicle.x
            dic['y']=dic['y'] + diffVehicle.y
            dic['yaw']=dic['yaw'] + diffVehicle.yaw
            dic['regenerated_health']=dic['regenerated_health']+diffVehicle.regenerated_health
            dic['regen_crew_hp_limit']=dic['regen_crew_hp_limit']+diffVehicle.regen_crew_hp_limit
            dic['regeneration_health']=dic['regeneration_health']+diffVehicle.regeneration_health
            
            currentEvt['evt_vehicle'][id]=toNamedTuple('Vehicle', dic)

        for id, plane in currentEvt['evt_plane'].items():
            plane: Plane
            diffPlane = diffData.planeDiff.get(id)
            diffPlane: PlaneDiff

            if diffPlane == None:
                logging.debug("diffPlane: id %s is none.", id)
                continue
            dic=plane._asdict()
            dic['position']=tuple([
                dic['position'][0]+diffPlane.x,
                dic['position'][1]+diffPlane.y]
            )

            currentEvt['evt_plane'][id]=toNamedTuple('Plane', dic)
        for i in range(len(currentEvt['evt_shot'])):
            shot = currentEvt['evt_shot'][i]
            id = shot.shot_id
            shot: Shot
            diffShot = diffData.shotDiff.get(id)
            diffShot: ShotDiff

            if diffShot == None:
                logging.debug("diffShot: id %s is none.", id)
                continue 
            dic=shot._asdict()
            origOrigin=dic['origin']
            origDest=dic['destnation']
            dic['origin']=tuple([origOrigin[0]+diffShot.origX,origOrigin[1]+diffShot.origY])
            dic['destnation']=tuple([origDest[0]+diffShot.destX,origDest[1]+diffShot.destY])
            currentEvt['evt_shot'][i]=toNamedTuple('Shot', dic)
        for id, torpedo in currentEvt['evt_torpedo'].items():
            torpedo: Torpedo
            diffTorpedo = diffData.torpedoDiff.get(id)
            diffTorpedo: TorpedoDiff

            if diffTorpedo == None:
                logging.debug("diffTorpedo: id %s is none.", id)
                continue 
            dic=torpedo._asdict()
            origOrigin=dic['origin']
            dic['origin']=tuple(origOrigin[0]+diffTorpedo.x,origOrigin[1]+diffTorpedo.y)
            dic['yaw']=dic['yaw']+diffTorpedo.yaw
            currentEvt['evt_torpedo'][id]=toNamedTuple('Torpedo', dic)
            
        for id, acoustic_torpedo in currentEvt['evt_acoustic_torpedo'].items():
            acoustic_torpedo: Torpedo
            diffAcousticTorpedo = diffData.acousticTorpedoDiff.get(id)
            diffAcousticTorpedo: AcousticTorpedoDiff

            if diffAcousticTorpedo == None:
                logging.debug("diffAcousticTorpedo: id %s is none.", id)
                continue 
            dic=acoustic_torpedo._asdict()
            dic['x']=dic['x']+diffAcousticTorpedo.x
            dic['y']=dic['y']+diffAcousticTorpedo.y
            dic['yaw']=dic['yaw']+diffTorpedo.yaw
            currentEvt['evt_acoustic_torpedo'][id]=toNamedTuple('AcousticTorpedo', dic)


def toNamedTuple(name: str, evt: dict):
        keyList=evt.keys()
        valueList=evt.values()
        tmpTuple=collections.namedtuple(name, keyList)
        return tmpTuple._make(valueList)
