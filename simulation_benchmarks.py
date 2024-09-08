import xml.etree.ElementTree as ET

if __name__ == "__main__":
    feed1 = "sim_cfg_grid_2_lanes/tripinfo.xml"
    feed2 = "sim_cfg_grid_2_lanes/tripinfo2.xml"
    
    try:
        tree1 = ET.parse(feed1)
        tree2 = ET.parse(feed2)
        root1 = tree1.getroot()
        root2 = tree2.getroot()
        tripinfos1 = root1.findall("tripinfo")
        tripinfos2 = root2.findall("tripinfo")     
    except Exception as e:
        print(f"Error: {e}")
        
    trips_1 = len(tripinfos1)
    trips_2 = len(tripinfos2)
        
    print(f"Total trips ended using platooning strategy: {trips_1}")
    total_waiting_time_1 = 0
    for tripinfo1 in tripinfos1:
        total_waiting_time_1 += float(tripinfo1.get("waitingTime"))
        #print(tripinfo1.get("waitingTime"))
        
    print(f"Total trips ended: {trips_2}")
    total_waiting_time_2 = 0
    for tripinfo2 in tripinfos2:
        total_waiting_time_2 += float(tripinfo2.get("waitingTime"))
        #print(tripinfo2.get("waitingTime"))
        
    trips_increment = trips_1 - trips_2
    percent_trips_increment = trips_increment * 100 / trips_2
    print(f"Trips increment by using platooning strategy: {round(percent_trips_increment, 2)}%\n")
    
    print(f"Total waiting time using platooning strategy: {round(total_waiting_time_1, 2)}")
    print(f"Total waiting time: {round(total_waiting_time_2, 2)}")
    
    waiting_time_reduction = total_waiting_time_2 - total_waiting_time_1
    percent_waiting_time_reduction = waiting_time_reduction * 100 / total_waiting_time_2
    print(f"Reduction of total waiting time by using platooning strategy: {round(percent_waiting_time_reduction, 2)}%")
    
    #import numpy as np
    #loss = 0
    '''
    b=[]
    for child in root1:
        a = float(child.attrib['timeLoss'])
        #list = [a]
        b.append(a)
        #print(list,' ')
    print(b)
    
    #Caculate average losstime
    loss = 0
    for child in root1:
        a = float(child.attrib['timeLoss'])
        loss += a
    ave_loss = loss / len(root1)
    print('ave_loss =', ave_loss)
    print('%.2f'%ave_loss)
    #Caculate average variance
    difference = 0
    for child in root1:
        a = float(child.attrib['timeLoss'])
        difference += (a - ave_loss)**2
    sigma = difference / len(root1)
    print('sigma =', sigma)
    print('%.2f'%sigma)
    print('The number of the vehicles is', len(root1))

    #Caculate average speed
    sum_v = 0
    for child in root1:
        v = float(child.attrib['arrivalSpeed'])
        sum_v += v
    ave_v = sum_v / len(root1)
    print('ave_v is', ave_v)
    print('%.2f'%ave_v)
    '''