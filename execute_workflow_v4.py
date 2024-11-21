'''
Created on 23/12/2021

@author: Eric

metashape.exe -r script.py > output.txt 2>&1
'''

import Metashape,os,re
import json,time,math
import numpy as np
from Lister_reconstructions_v1 import lister_caract_projet_psx
import ftplib
from download_ftp_tree import download_ftp_tree
from Photogrammetrie_multispectrale_v1 import photogrammetrie_multispectrale
from Photogrammetrie_RGB_v1 import photogrammetrie_RGB

progess_print_old=0
temps_debut=time.time()
Metashape.app.cpu_enable=True

'''
def getFolderSize(folder):
    #return size in octets
    total_size = os.path.getsize(folder)
    for item in os.listdir(folder):
        itempath = os.path.join(folder, item)
        if os.path.isfile(itempath):
            total_size += os.path.getsize(itempath)
        elif os.path.isdir(itempath):
            total_size += getFolderSize(itempath)
    return total_size

##print ("Size: " + str(getFolderSize("I:\\test\\Archiduo\\2021_12_09\\flow")))



def progress_print(p):
    global etape_wkf,nb_etape_wkf,progess_print_old,temps_debut
    #print('Current task progress: {:.2f}%'.format(p))
    if float(p)> progess_print_old:
        temps_flow=time.time()-temps_debut
        temps_flow_str=time.strftime("%Hh %Mm",time.gmtime(temps_flow))
        print('/r/nsortie_metashape:status:En cours:{:.2f}:{}/{}:{}:/r/n'.format(p,etape_wkf,nb_etape_wkf,temps_flow_str))
    progess_print_old=float(p)+1.

def calcul_erreur_marker(doc):
    chk = doc.chunk
    result = []
    for marker in chk.markers:
        positions = []
        num_projections = len(marker.projections)
        if num_projections>1:
            if len(marker.projections.items())!=0:
                positions=np.array(chk.crs.project(chk.transform.matrix.mulp(marker.position))-marker.reference.location)
                result.append(positions)
    return result


def upload_ftp(file_name,local_path,dest_path):
    msg=""
    #dest_path='Data/Lucos_ble/2022_02_03/'
    #local_path='D:\\Data\\Lucos_ble\\2022_02_03\\flow\\'
    if os.path.isfile(local_path+file_name):
        ftp_nas=create_ftp()
        for d in dest_path.split('/'):
            if not d=="":
                try :                                   
                    ftp_nas.cwd(d)
                except ftplib.error_perm:
                    ftp_nas.mkd(d)            
                    ftp_nas.cwd(d)
        try :
            ftp_nas.storbinary( 'STOR '+file_name, open(os.path.join(local_path,file_name), 'rb') )
            msg="copie_ok"
        except Exception as e:
            msg=e
    return msg
'''

arg=input()
#arg='{"id_donnees":1675421307357,"date_donnees":"2023/02/02","date":"03/02/2023 11:48:28","etape":"0/1","status":"Donnees sur Nas","color_status":"#ffffff","workflow":"MatchPhotos,","progression":0,"nom_op":"EROY","nom_expe":"Lami_Val","vecteur":"Drone","camera":"Camera_multispectrale","path_dest_nas":"//192.168.0.2/Phenotypage/Data/","path_dest_local":"D:/Data/","path_dest_expe":"Lami_Val/2023_02_02/","path_dest_donnees":"Lami_Val/2023_02_02/Drone/Camera_multispectrale/","path_dest_flow":"Lami_Val/2023_02_02/flow/","size_donnees":"9.68","flag_data_local":false}'

dico_donnees = json.loads('{}'.format(arg))

if dico_donnees['camera']=='Camera_RGB':
    photogrammetrie_RGB(dico_donnees)
elif dico_donnees['camera']=='Camera_multispectrale':
    photogrammetrie_multispectrale(dico_donnees)
