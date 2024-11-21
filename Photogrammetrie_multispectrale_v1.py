'''
Created on 03/03/2023

@author: Eric ROY

'''

import Metashape,os,re
import json,time,math
import numpy as np
from Lister_reconstructions_v1 import lister_caract_projet_psx
import ftplib
from download_ftp_tree import download_ftp_tree
from Photogrammetrie_RGB_v1 import getFolderSize,create_ftp,upload_ftp,calcul_erreur_marker

progess_print_old=0
temps_debut=time.time()
Metashape.app.cpu_enable=True



def progress_print(p):
    global etape_wkf,nb_etape_wkf,progess_print_old,temps_debut
    #print('Current task progress: {:.2f}%'.format(p))
    if float(p)> progess_print_old:
        temps_flow=time.time()-temps_debut
        temps_flow_str=time.strftime("%Hh %Mm",time.gmtime(temps_flow))
        print('/r/nsortie_metashape:status:En cours:{:.2f}:{}/{}:{}:/r/n'.format(p,etape_wkf,nb_etape_wkf,temps_flow_str))
    progess_print_old=float(p)+1.



def photogrammetrie_multispectrale(dico_donnees):
    global temps_debut,etape_wkf,nb_etape_wkf
    temps_debut=time.time()
    msg_erreur=""
    
    #print(dico_donnees)
    dico_donnees['path_dest_nas']=dico_donnees['path_dest_nas'].replace('/','\\')
    dico_donnees['path_dest_nas']=dico_donnees['path_dest_nas'].replace('\\\\','\\')
    dico_donnees['path_dest_local']=dico_donnees['path_dest_local'].replace('/','\\')
    dico_donnees['path_dest_expe']=dico_donnees['path_dest_expe'].replace('/','\\')
    dico_donnees['path_dest_flow']=dico_donnees['path_dest_flow'].replace('/','\\')
    dico_donnees['path_dest_donnees']=dico_donnees['path_dest_donnees'].replace('/','\\')
    dico_donnees['path_dest_donnees_locale']=os.path.join(dico_donnees['path_dest_local'],dico_donnees['path_dest_donnees']).replace('\\','/')

    dico_donnees['date_donnees']=dico_donnees['date_donnees'].replace('/','_')

    list_wkf=dico_donnees['workflow'].split(',')
    list_wkf.remove('')
    dico_donnees['workflow']=list_wkf
    etape_wkf=0     #int(dico_donnees['etape'].split('/')[0])
    nb_etape_wkf=len(dico_donnees['workflow'])*2
    ftp_path_racine='Data/'

    rmse_xyz=""
    erreur_X=""
    erreur_Y=""
    erreur_Z=""
    print("/r/nsortie_metashape:status:{}:0:{}/{}:/r/n".format("Debut",etape_wkf,nb_etape_wkf))

    ########## Copie en local des donnees   #############

    try:
        if not(os.path.isdir(dico_donnees['path_dest_local']+dico_donnees['nom_expe'])):
            os.mkdir(dico_donnees['path_dest_local']+dico_donnees['nom_expe'])
        if not(os.path.isdir(dico_donnees['path_dest_local']+dico_donnees['path_dest_expe'])):
            os.mkdir(dico_donnees['path_dest_local']+dico_donnees['path_dest_expe'])

        if not(os.path.isdir(dico_donnees['path_dest_local']+dico_donnees['path_dest_donnees'])):
            ftp_nas=create_ftp()
            remote_dir = ftp_path_racine+dico_donnees['path_dest_expe'].replace('\\','/')
            local_dir = dico_donnees['path_dest_local']+dico_donnees['path_dest_expe']
            download_ftp_tree(ftp_nas, remote_dir, local_dir, overwrite=False, guess_by_extension=True)
            ftp_nas.close()
            size_donnees=getFolderSize(local_dir)/1e9
            print("/r/nsortie_metashape:status:{}:0:{}/{}:{}/r/n".format("data_local",etape_wkf,nb_etape_wkf,True))

        else:
            local_dir = dico_donnees['path_dest_local']+dico_donnees['path_dest_expe']
            size_donnees=getFolderSize(local_dir)/1e9
            print("/r/nsortie_metashape:status:{}:0:{}/{}:{}/r/n".format("data_local",etape_wkf,nb_etape_wkf,True))

        ftp_nas=create_ftp()
        remote_dir = ftp_path_racine+dico_donnees['nom_expe']+'/config'
        local_dir = dico_donnees['path_dest_local']+dico_donnees['nom_expe']+'\\config'
        download_ftp_tree(ftp_nas, remote_dir, local_dir, overwrite=True, guess_by_extension=True)
        ftp_nas.close()
    except Exception as e:
        msg_erreur=e
        print("/r/nsortie_metashape:erreur:{}::{}/{}:/r/n".format("probleme copie fichier en local ftp",etape_wkf,nb_etape_wkf))

    local_dir=dico_donnees['path_dest_local']+dico_donnees['path_dest_expe']+"flow\\"
    remote_dir = ftp_path_racine+dico_donnees['path_dest_expe'].replace('\\','/')+"flow/"

    try :
        f_config_expe = open(os.path.join(dico_donnees['path_dest_local']+dico_donnees['nom_expe']+'\\config','config_expe.json'))
        dico_config_expe = json.load(f_config_expe)
        f_config_expe.close()
    except Exception as e:
        msg_erreur=e
        print("/r/nsortie_metashape:erreur:{}::{}/{}:/r/n".format("probleme fichier config expe",etape_wkf,nb_etape_wkf))

    try:
        if dico_config_expe['mode_repere']=='aucun':
            file_pts_ref=""
        elif dico_config_expe['mode_repere']=='manuel':
            file_pts_ref=os.path.join(dico_donnees['path_dest_local']+dico_donnees['nom_expe']+'\\config',dico_config_expe['nom_fichier_ref'])

        if not(os.path.isdir(os.path.join(dico_donnees['path_dest_local'],dico_donnees['path_dest_flow']))):
            os.mkdir(os.path.join(dico_donnees['path_dest_local'],dico_donnees['path_dest_flow']))
        #name_doc_save='{}_{}.psx'.format(dico_donnees['nom_expe'],dico_donnees['date_donnees'])
        #print("sortie_metashape:",dico_donnees['path_dest_flow'],name_doc_save)

        doc  = Metashape.Document()
        name_file_psx='{}{}_{}.psx'.format(os.path.join(dico_donnees['path_dest_local'],dico_donnees['path_dest_flow']),dico_donnees['nom_expe'],dico_donnees['date_donnees'])

        list_chunk=[[0,dico_donnees['nom_expe'],'.TIF'],[1,dico_donnees['nom_expe']+"_RGB",'.JPG']]
        
        ############## Match photo  #############
        if not os.path.isfile(name_file_psx):

            doc.save(name_file_psx)
            
            while len(doc.chunks)!=len(list_chunk):
                doc.addChunk()
            for n_chk in list_chunk:
                #Création du chunck si absent
                chk =doc.chunks[n_chk[0]]
                chk.label=n_chk[1]
                try :

                    #Liste les photos a inserer
                    liste_fichier_brute=os.listdir(dico_donnees['path_dest_donnees_locale'])
                    list_file_image=[]
                    for h in liste_fichier_brute:
                        if os.path.isdir(os.path.join(dico_donnees['path_dest_donnees_locale'],h))==True:
                            #print (os.path.join(dico_donnees['path_dest_donnees'],h))
                            for f in os.listdir(os.path.join(dico_donnees['path_dest_donnees_locale'],h)):
                                if f[-4:]==n_chk[2] :
                                    list_file_image.append(os.path.join(dico_donnees['path_dest_donnees_locale'],h,f))
                        else:
                            if h[-4:]==n_chk[2] :
                                list_file_image.append(os.path.join(dico_donnees['path_dest_donnees_locale'],h))
                    #print ("sortie_metashape: Nombre d'image a traiter : {}".format(len(list_file_image)))
                    chk.addPhotos(list_file_image[:],load_xmp_accuracy=True)
                except Exception as e:
                    msg_erreur=e
                    print("/r/nsortie_metashape:erreur:{}::{}/{}:/r/n".format("probleme ajout des photos",etape_wkf,nb_etape_wkf))


                try:
                    #Definit le crs du projet en wgs84
                    chk.crs = Metashape.CoordinateSystem("EPSG::4326")
                    #Convertit le crs des camera de wgs84 en lambert 93 puis decoche les references cameras
                    #print (chk.cameras)
                    crs_lbt93 = Metashape.CoordinateSystem(dico_config_expe['crs'])
                    for cam in chk.cameras:
                        if cam.reference.location:
                            cam.reference.location=crs_lbt93.project(chk.crs.unproject(cam.reference.location))
                        #cam.reference.enabled=False

                    #Change la precision des cameras
                    #print (chk.camera_location_accuracy)
                    #chk.camera_location_accuracy=(50.,50.,50.)
                    #chk.marker_location_accuracy=(0.005,0.005,0.005)
                    #print (chk.camera_location_accuracy)

                    #Change le crs du projet en lambert 93
                    chk.crs = Metashape.CoordinateSystem(dico_config_expe['crs'])
                    if dico_config_expe['mode_repere']=='auto':
                        chk.detectMarkers(target_type=Metashape.CircularTarget14bit, tolerance=50)
                        chk.importReference(file_pts_ref, Metashape.ReferenceFormat.ReferenceFormatCSV , columns=dico_config_expe['ref_format'],    \
                                            delimiter=dico_config_expe['ref_separator'],group_delimiters=False, skip_rows=1,   \
                                            crs=Metashape.CoordinateSystem(dico_config_expe['crs']), \
                                            ignore_labels=False, create_markers=False)
                        # for mrk in chk.markers:
                        #     mrk.reference.enabled=True
                    elif dico_config_expe['mode_repere']=='manuel':
                        chk.importReference(file_pts_ref, Metashape.ReferenceFormat.ReferenceFormatCSV , columns=dico_config_expe['ref_format'],    \
                                        delimiter=dico_config_expe['ref_separator'],group_delimiters=False, skip_rows=1,   \
                                        items=Metashape.ReferenceItems.ReferenceItemsMarkers,crs=Metashape.CoordinateSystem(dico_config_expe['crs']), \
                                        ignore_labels=False, create_markers=True)
                    elif dico_config_expe['mode_repere']=='aucun':
                        pass

                    doc.save()
                except Exception as e:
                    msg_erreur=e
                    print("/r/nsortie_metashape:erreur:{}::{}/{}:/r/n".format("probleme parametrage systeme coordonnees",etape_wkf,nb_etape_wkf))

                '''
                #start_time = time.time()
                if msg_erreur=="":
                    try :
                        chk.matchPhotos(downscale=dico_config_expe['matchphotos_downscale'], generic_preselection=True,reference_preselection=True,    \
                                        keypoint_limit=40000, tiepoint_limit=4000,progress=progress_print)
                        chk.alignCameras(reset_alignment=True,adaptive_fitting=True,progress=progress_print)
                        doc.save()
                        chk.matchPhotos(downscale=dico_config_expe['matchphotos_downscale'], generic_preselection=True,reference_preselection=True,    \
                                        keypoint_limit=40000, tiepoint_limit=4000,progress=progress_print)
                        chk.alignCameras(reset_alignment=False,adaptive_fitting=True,progress=progress_print)
                        doc.save()
                        chk.matchPhotos(downscale=dico_config_expe['matchphotos_downscale'], generic_preselection=True,reference_preselection=True,    \
                                        keypoint_limit=40000, tiepoint_limit=4000,progress=progress_print)
                        chk.alignCameras(reset_alignment=False,adaptive_fitting=True,progress=progress_print)
                        doc.save()
                        chk.calibrateReflectance(use_reflectance_panels=False, use_sun_sensor=True, progress=progress_print)
                        doc.save()
                        try:
                            path_file_report=os.path.join(dico_donnees['path_dest_local'],dico_donnees['path_dest_flow']) +'\\'
                            name_file_report='{}_{}_rapport.pdf'.format(n_chk[1],dico_donnees['date_donnees'])
                            chk.exportReport(path_file_report+name_file_report)
                            upload_ftp(name_file_report,path_file_report,ftp_path_racine+dico_donnees['path_dest_flow'].replace('\\','/'))

                        except Exception as e:
                            msg_erreur=e
                            print("/r/nsortie_metashape:warning:impossible d'exporter le rapport::{}/{}:/r/n".format(etape_wkf,nb_etape_wkf))
                        print('/r/nsortie_metashape:status:Fin:{:.2f}:{}/{}:{:.2f}:/r/n'.format(100,etape_wkf,nb_etape_wkf,getFolderSize(local_dir)/1e9))
                        etape_wkf+=1
                    except Exception as e:
                        msg_erreur=e
                        #print("Aborted by user")
                        print(e)
                        print("sortie_metashape:erreur:{}::{}/{}:".format("probleme alignement des cameras ",etape_wkf,nb_etape_wkf))
                        doc.save()
                '''
        del doc
        doc  = Metashape.Document()


        if ('MatchPhotos' in list_wkf or 'Densecloud' in list_wkf or 'Mnt' in list_wkf or 'Ortho' in list_wkf) and msg_erreur=="":
            print("/r/nsortie_metashape:status:{}:0:{}/{}:/r/n".format("Debut",etape_wkf,nb_etape_wkf))
            if os.path.isfile(name_file_psx):
                doc.open(name_file_psx)
                try :
                    doc.save()
                except :
                    doc.save(name_file_psx)
                
                for n_chk in list_chunk:
                    chk =doc.chunks[n_chk[0]]
                    if chk:
                        # test match photos
                        if not chk.point_cloud:
                            try :
                                for cam in chk.cameras:
                                    cam.reference.enabled=True

                                chk.matchPhotos(downscale=dico_config_expe['matchphotos_downscale'], generic_preselection=True,reference_preselection=True,    \
                                                keypoint_limit=40000, tiepoint_limit=4000,progress=progress_print)
                                chk.alignCameras(reset_alignment=True,adaptive_fitting=True,progress=progress_print)
                                doc.save()
                                chk.matchPhotos(downscale=dico_config_expe['matchphotos_downscale'], generic_preselection=True,reference_preselection=True,    \
                                                keypoint_limit=40000, tiepoint_limit=4000,progress=progress_print)
                                chk.alignCameras(reset_alignment=False,adaptive_fitting=True,progress=progress_print)
                                doc.save()
                                chk.matchPhotos(downscale=dico_config_expe['matchphotos_downscale'], generic_preselection=True,reference_preselection=True,    \
                                                keypoint_limit=40000, tiepoint_limit=4000,progress=progress_print)
                                chk.alignCameras(reset_alignment=False,adaptive_fitting=True,progress=progress_print)
                                doc.save()
                                # chk.calibrateReflectance(use_reflectance_panels=False, use_sun_sensor=True, progress=progress_print)
                                doc.save()
                                try:
                                    path_file_report=os.path.join(dico_donnees['path_dest_local'],dico_donnees['path_dest_flow']) +'\\'
                                    name_file_report='{}_{}_rapport.pdf'.format(n_chk[1],dico_donnees['date_donnees'])
                                    chk.exportReport(path_file_report+name_file_report)
                                    upload_ftp(name_file_report,path_file_report,ftp_path_racine+dico_donnees['path_dest_flow'].replace('\\','/'))

                                except Exception as e:
                                    msg_erreur=e
                                    print("/r/nsortie_metashape:warning:impossible d'exporter le rapport::{}/{}:/r/n".format(etape_wkf,nb_etape_wkf))
                                print('/r/nsortie_metashape:status:{}-Fin:{:.2f}:{}/{}:{:.2f}:/r/n'.format(chk.label,100,etape_wkf,nb_etape_wkf,getFolderSize(local_dir)/1e9))
                                etape_wkf+=1
                            except Exception as e:
                                msg_erreur=e
                                print("sortie_metashape:erreur:{}-{}::{}/{}:".format(chk.label,"probleme alignement des cameras ",etape_wkf,nb_etape_wkf))
                                doc.save()
                        else:
                            etape_wkf+=1
                        
                        
                        if chk.label==n_chk[1]:
                            # for cam in chk.cameras:
                            #     cam.reference.enabled=False
                            markers_errors=calcul_erreur_marker(doc,n_chk[0])
                            if markers_errors or dico_config_expe['mode_repere']=='aucun':
                                if not chk.orthomosaic or not chk.elevation :    #not chk.meta['OptimizeCameras/duration']:
                                    try :
                                        SinRotZ= math.sin(math.radians(dico_config_expe['RotZDeg']))
                                        CosRotZ= math.cos(math.radians(dico_config_expe['RotZDeg']))
                                        reg_mat = Metashape.Matrix([[CosRotZ,-SinRotZ,0,0],[SinRotZ,CosRotZ,0,0],[0,0,1,0],[0,0,0,1]])
                                        reg_center=Metashape.Vector(dico_config_expe['reg_center'])
                                        reg_size=Metashape.Vector(dico_config_expe['reg_size'])
                                        dico_config_expe['reg_param']=[reg_center,reg_size,reg_mat]
                                        if dico_config_expe['reg_param'][0]!="":

                                            try :
                                                chk.updateTransform()
                                                chk.optimizeCameras(fit_f=True,fit_cx=True,fit_cy=True,fit_b1=True,fit_b2=True,fit_k1=True,fit_k2=True,fit_k3=True,fit_k4=True,fit_p1=True,fit_p2=True,fit_p3=True,fit_p4=True,adaptive_fitting=True,tiepoint_covariance=False,progress=progress_print)
                                                chk.resetRegion()
                                                T = chk.transform.matrix
                                                S = chk.transform.scale
                                                crs = chk.crs
                                                region = chk.region
                                                region.center = T.inv().mulp(crs.unproject(dico_config_expe['reg_param'][0]))
                                                region.size = dico_config_expe['reg_param'][1] / S

                                                v = Metashape.Vector( [0,0,0,1] )
                                                v_t = T * v
                                                v_t.size = 3
                                                m = chk.crs.localframe(v_t)
                                                m = m * T
                                                m = dico_config_expe['reg_param'][2]*m
                                                s = math.sqrt(m[0,0]**2 + m[0,1]**2 + m[0,2]**2) #scale factor
                                                R = Metashape.Matrix( [[m[0,0],m[0,1],m[0,2]], [m[1,0],m[1,1],m[1,2]], [m[2,0],m[2,1],m[2,2]]])
                                                R = R * (1. / s)
                                                region.rot = R.t()
                                                chk.region = region
                                                doc.save()

                                            except Exception as e:
                                                print("sortie_metashape:erreur:{}-{}::{}/{}:".format(chk.label,"probleme optimisation ou region",etape_wkf,nb_etape_wkf))
                                                msg_erreur=e
                                    except:
                                        pass
                                
                                if dico_config_expe['mode_repere']!='aucun':
                                    markers_errors=calcul_erreur_marker(doc,n_chk[0])
                                    #print (markers_errors)
                                    array_markers=np.array(markers_errors)
                                    rmse_xyz=np.sqrt(np.mean(array_markers[:,0]**2+array_markers[:,1]**2+array_markers[:,2]**2))
                                    if rmse_xyz>=dico_config_expe['rmse_xyz']:
                                        print("/r/nsortie_metashape:warning:erreur rmse_xyz>{}::{}/{}:/r/n".format(dico_config_expe['rmse_xyz'],etape_wkf,nb_etape_wkf))

                                    name_file_markers='{}_{}_markers.xml'.format(n_chk[1],dico_donnees['date_donnees'])
                                    path_file_markers=os.path.join(dico_donnees['path_dest_local'],dico_donnees['path_dest_flow'])
                                
                                    if not os.path.isfile(path_file_markers+name_file_markers):
                                        try:
                                            chk.exportMarkers(path_file_markers+name_file_markers)
                                            upload_ftp(name_file_markers,path_file_markers,ftp_path_racine+dico_donnees['path_dest_flow'].replace('\\','/'))
                                            try:
                                                path_file_report=os.path.join(dico_donnees['path_dest_local'],dico_donnees['path_dest_flow'])
                                                name_file_report='{}_{}_rapport.pdf'.format(n_chk[1],dico_donnees['date_donnees'])
                                                chk.exportReport(path_file_report+name_file_report)
                                                upload_ftp(name_file_report,path_file_report,ftp_path_racine+dico_donnees['path_dest_flow'].replace('\\','/'))

                                            except Exception as e:
                                                msg_erreur=e
                                                print("/r/nsortie_metashape:warning:impossible d'exporter le rapport::{}/{}:/r/n".format(etape_wkf,nb_etape_wkf))
                                        except Exception as e:
                                            msg_erreur=e
                                            print("/r/nsortie_metashape:warning:impossible d'exporter les markers::{}/{}:/r/n".format(etape_wkf,nb_etape_wkf))

                                if 'Ortho' in list_wkf and msg_erreur=="":
                                    print("/r/nsortie_metashape:status:{}:0:{}/{}:/r/n".format("Debut",etape_wkf,nb_etape_wkf))
                                    if dico_config_expe['param_dem']['Xmin']!=None:
                                        parametre_dem=[[dico_config_expe['param_dem']['Xmin'],dico_config_expe['param_dem']['Ymin'],dico_config_expe['param_dem']['Xmax'],dico_config_expe['param_dem']['Ymax']],dico_config_expe['param_dem']['resolution']]
                                        region_dem = Metashape.BBox()
                                        region_dem.min = Metashape.Vector(parametre_dem[0][:2])
                                        region_dem.max = Metashape.Vector(parametre_dem[0][2:])
                                    
                                    if not chk.orthomosaic:
                                        try:
                                            chk.buildDem(source_data=Metashape.PointCloudData,interpolation=Metashape.EnabledInterpolation,classes=[0,1,3,4,5],progress=progress_print)
                                            doc.save()
                                            chk.buildOrthomosaic(surface_data=Metashape.ElevationData, blending_mode=Metashape.MosaicBlending,fill_holes=True,progress=progress_print)
                                            doc.save()
                                            #chk.orthomosaic.removeOrthophotos()
                                            doc.save()
                                            print('/r/nsortie_metashape:status:Fin:{:.2f}:{}/{}:{:.2f}:/r/n'.format(100,etape_wkf,nb_etape_wkf,getFolderSize(local_dir)/1e9))
                                            etape_wkf+=1
                                        except Exception as e:
                                            msg_erreur=e
                                            print("sortie_metashape:erreur:{}-{}::{}/{}:".format(chk.label,"probleme orthomosaique",etape_wkf,nb_etape_wkf))
                                    else:
                                        print('/r/nsortie_metashape:status:Fin:{:.2f}:{}/{}:{:.2f}:/r/n'.format(100,etape_wkf,nb_etape_wkf,getFolderSize(local_dir)/1e9))
                                        etape_wkf+=1

                                    
                                
                                    if 'Densecloud' in list_wkf and msg_erreur=="":
                                        print("/r/nsortie_metashape:status:{}-{}:0:{}/{}:/r/n".format(chk.label,"Debut",etape_wkf,nb_etape_wkf))
                                        if not chk.dense_cloud:

                                            try:
                                                if chk.elevation:
                                                    chk.elevation.clear()

                                                if not chk.depth_maps :
                                                    chk.buildDepthMaps(downscale=dico_config_expe['depthmaps_downscale'], filter_mode=Metashape.NoFiltering, reuse_depth=True,progress=progress_print)
                                                    doc.save()
                                                chk.buildDenseCloud(point_colors=True, point_confidence=True,keep_depth=True, max_neighbors=100,progress=progress_print)
                                                doc.save()

                                                time.sleep(1)

                                                chk.dense_cloud.assignClass(1,list(range(128)))
                                                chk.dense_cloud.resetFilters()
                                                time.sleep(5)
                                                chk.dense_cloud.setConfidenceFilter(0,2)
                                                #chk.dense_cloud.setClassesFilter(0)
                                                chk.dense_cloud.assignClass(18,1)
                                                #time.sleep(1)
                                                chk.dense_cloud.setClassesFilter(18)
                                                chk.dense_cloud.resetFilters()

                                                chk.dense_cloud.setConfidenceFilter(3,5)
                                                chk.dense_cloud.assignClass(3,1)
                                                chk.dense_cloud.setClassesFilter(3)
                                                chk.dense_cloud.resetFilters()

                                                chk.dense_cloud.setConfidenceFilter(6,10)
                                                chk.dense_cloud.assignClass(4,1)
                                                chk.dense_cloud.setClassesFilter(4)
                                                chk.dense_cloud.resetFilters()

                                                chk.dense_cloud.setConfidenceFilter(11,255)
                                                chk.dense_cloud.assignClass(5,1)
                                                chk.dense_cloud.setClassesFilter(5)
                                                chk.dense_cloud.resetFilters()
                                                doc.save()
                                                try:
                                                    path_file_report=os.path.join(dico_donnees['path_dest_local'],dico_donnees['path_dest_flow'])
                                                    name_file_report='{}_{}_rapport.pdf'.format(n_chk[1],dico_donnees['date_donnees'])
                                                    chk.exportReport(path_file_report+name_file_report)
                                                    upload_ftp(name_file_report,path_file_report,ftp_path_racine+dico_donnees['path_dest_flow'].replace('\\','/'))
                                                except Exception as e:
                                                    print("/r/nsortie_metashape:warning:impossible d'exporter le rapport::{}/{}:/r/n".format(etape_wkf,nb_etape_wkf))
                                                print('/r/nsortie_metashape:status:Fin:{:.2f}:{}/{}:{:.2f}:/r/n'.format(100,etape_wkf,nb_etape_wkf,getFolderSize(local_dir)/1e9))
                                                etape_wkf+=1
                                            except Exception as e:
                                                msg_erreur=e
                                                print("sortie_metashape:erreur:{}::{}/{}:".format("probleme nuage dense",etape_wkf,nb_etape_wkf))
                                        else:
                                            etape_wkf+=1
                                    

                                    if 'Mnt' in list_wkf and msg_erreur=="":
                                        print("/r/nsortie_metashape:status:{}:0:{}/{}:/r/n".format("Debut",etape_wkf,nb_etape_wkf))
                                        parametre_dem=[[dico_config_expe['param_dem']['Xmin'],dico_config_expe['param_dem']['Ymin'],dico_config_expe['param_dem']['Xmax'],dico_config_expe['param_dem']['Ymax']],dico_config_expe['param_dem']['resolution']]
                                        region_dem = Metashape.BBox()
                                        region_dem.min = Metashape.Vector(parametre_dem[0][:2])
                                        region_dem.max = Metashape.Vector(parametre_dem[0][2:])

                                        if not chk.elevation:
                                            try:
                                                chk.buildDem(source_data=Metashape.PointCloudData,interpolation=Metashape.DisabledInterpolation,classes=[0,1,3,4,5],progress=progress_print)
                                                doc.save()
                                            except Exception as e:
                                                msg_erreur=e
                                                print("sortie_metashape:erreur:{}::{}/{}:".format("probleme creation mnt",etape_wkf,nb_etape_wkf))

                                        name_file_mnt='{}_{}_mnt.tif'.format(n_chk[1],dico_donnees['date_donnees'])
                                        path_file_mnt=os.path.join(dico_donnees['path_dest_local'],dico_donnees['path_dest_flow'])
                                        if not os.path.isfile(path_file_mnt+name_file_mnt):
                                            try:
                                                chk.exportRaster(path_file_mnt+name_file_mnt,region=region_dem, resolution_x=parametre_dem[1],resolution_y=parametre_dem[1],source_data=Metashape.ElevationData)
                                                upload_ftp(name_file_mnt,path_file_mnt,ftp_path_racine+dico_donnees['path_dest_flow'].replace('\\','/'))
                                                
                                                try:
                                                    path_file_report=os.path.join(dico_donnees['path_dest_local'],dico_donnees['path_dest_flow'])
                                                    name_file_report='{}_{}_rapport.pdf'.format(n_chk[1],dico_donnees['date_donnees'])
                                                    chk.exportReport(path_file_report+name_file_report)
                                                    upload_ftp(name_file_report,path_file_report,ftp_path_racine+dico_donnees['path_dest_flow'].replace('\\','/'))
                                                except Exception as e:
                                                    msg_erreur=e
                                                    print("/r/nsortie_metashape:warning:impossible d'exporter le rapport::{}/{}:/r/n".format(etape_wkf,nb_etape_wkf))
                                                print('/r/nsortie_metashape:status:Fin:{:.2f}:{}/{}:{:.2f}:/r/n'.format(100,etape_wkf,nb_etape_wkf,getFolderSize(local_dir)/1e9))
                                                etape_wkf+=1
                                            except Exception as e:
                                                msg_erreur=e
                                                print("sortie_metashape:erreur:{}::{}/{}:".format("probleme export mnt",etape_wkf,nb_etape_wkf))
                                        else:
                                            etape_wkf+=1
                                

                                elif 'Mnt' in list_wkf and msg_erreur=="":
                                    print("/r/nsortie_metashape:status:{}:0:{}/{}:/r/n".format("Debut",etape_wkf,nb_etape_wkf))
                                    parametre_dem=[[dico_config_expe['param_dem']['Xmin'],dico_config_expe['param_dem']['Ymin'],dico_config_expe['param_dem']['Xmax'],dico_config_expe['param_dem']['Ymax']],dico_config_expe['param_dem']['resolution']]
                                    region_dem = Metashape.BBox()
                                    region_dem.min = Metashape.Vector(parametre_dem[0][:2])
                                    region_dem.max = Metashape.Vector(parametre_dem[0][2:])
                                    if not chk.elevation:
                                        try:

                                            chk.buildDem(source_data=Metashape.PointCloudData,interpolation=Metashape.EnabledInterpolation,classes=[0,1,3,4,5],progress=progress_print)
                                            doc.save()
                                        except Exception as e:
                                            msg_erreur=e
                                            print("sortie_metashape:erreur:{}::{}/{}:".format("probleme creation mnt",etape_wkf,nb_etape_wkf))

                                    name_file_mnt='{}_{}_mnt.tif'.format(n_chk[1],dico_donnees['date_donnees'])
                                    path_file_mnt=os.path.join(dico_donnees['path_dest_local'],dico_donnees['path_dest_flow'])
                                    if not os.path.isfile(path_file_mnt+name_file_mnt):
                                        try:
                                            chk.exportRaster(path_file_mnt+name_file_mnt,region=region_dem, resolution_x=parametre_dem[1],resolution_y=parametre_dem[1],source_data=Metashape.ElevationData)
                                            upload_ftp(name_file_mnt,path_file_mnt,ftp_path_racine+dico_donnees['path_dest_flow'].replace('\\','/'))

                                            try:
                                                path_file_report=os.path.join(dico_donnees['path_dest_local'],dico_donnees['path_dest_flow'])
                                                name_file_report='{}_{}_rapport.pdf'.format(n_chk[1],dico_donnees['date_donnees'])
                                                chk.exportReport(path_file_report+name_file_report)
                                                upload_ftp(name_file_report,path_file_report,ftp_path_racine+dico_donnees['path_dest_flow'].replace('\\','/'))
                                            except Exception as e:
                                                print("/r/nsortie_metashape:warning:impossible d'exporter le rapport::{}/{}:/r/n".format(etape_wkf,nb_etape_wkf))
                                            print('/r/nsortie_metashape:status:Fin:{:.2f}:{}/{}:{:.2f}:/r/n'.format(100,etape_wkf,nb_etape_wkf,getFolderSize(local_dir)/1e9))
                                            etape_wkf+=1

                                        except Exception as e:
                                            msg_erreur=e
                                            print("sortie_metashape:erreur:{}::{}/{}:".format("probleme export mnt",etape_wkf,nb_etape_wkf))
                                    else:
                                        etape_wkf+=1
                                

                            else:
                                print("/r/nsortie_metashape:erreur:{}-Veuillez placer les reperes::{}/{}:/r/n".format(chk.label,etape_wkf,nb_etape_wkf))
                                #msg_erreur='Veuillez placer les reperes!'

                    name_file_caract='{}_{}_caract.json'.format(n_chk[1],dico_donnees['date_donnees'])
                    path_file_caract=os.path.join(dico_donnees['path_dest_local'],dico_donnees['path_dest_flow'])
                    caract_projet=lister_caract_projet_psx(name_file_psx)
                    try:
                        erreur_X=caract_projet[0]['Projections/Xmax']-caract_projet[0]['Projections/Xmin']
                        erreur_Y=caract_projet[0]['Projections/Ymax']-caract_projet[0]['Projections/Ymin']
                        erreur_Z=caract_projet[0]['Projections/Zmax']-caract_projet[0]['Projections/Zmin']
                    except:
                        pass
                    with open(path_file_caract+name_file_caract, 'w') as f:
                        json.dump(caract_projet[0], f, ensure_ascii=False)
                    upload_ftp(name_file_caract,path_file_caract,ftp_path_racine+dico_donnees['path_dest_flow'].replace('\\','/'))
                        

        if 'Export' in list_wkf :
            print("/r/nsortie_metashape:status:{}:0:{}/{}:/r/n".format("Debut",etape_wkf,nb_etape_wkf))
            if os.path.isfile(name_file_psx):
                doc.open(name_file_psx)
                try :
                    doc.save()
                except :
                    doc.save(name_file_psx)
                #Chunk multispect
                n_chk=list_chunk[0]
                chk =doc.chunks[n_chk[0]]
                
                #export markers
                name_file_markers='{}_{}_markers.xml'.format(n_chk[1],dico_donnees['date_donnees'])
                path_file_markers=os.path.join(dico_donnees['path_dest_local'],dico_donnees['path_dest_flow'])
                if not os.path.isfile(path_file_markers+name_file_markers):
                    try:
                        if chk.markers!=[]:
                            chk.exportMarkers(path_file_markers+name_file_markers)
                            upload_ftp(name_file_markers,path_file_markers,ftp_path_racine+dico_donnees['path_dest_flow'].replace('\\','/'))
                    except Exception as e:
                        msg_erreur=e
                        print("/r/nsortie_metashape:warning:impossible d'exporter les markers::{}/{}:/r/n".format(etape_wkf,nb_etape_wkf))

                #export ortho reflectance
                try:
                    parametre_dem=[[dico_config_expe['param_dem']['Xmin'],dico_config_expe['param_dem']['Ymin'],dico_config_expe['param_dem']['Xmax'],dico_config_expe['param_dem']['Ymax']],dico_config_expe['param_dem']['resolution']]
                    region_dem = Metashape.BBox()
                    region_dem.min = Metashape.Vector(parametre_dem[0][:2])
                    region_dem.max = Metashape.Vector(parametre_dem[0][2:])
                    name_file_ortho='{}_{}_ortho_reflectance.tif'.format(n_chk[1],dico_donnees['date_donnees'])
                    path_file_ortho=os.path.join(dico_donnees['path_dest_local'],dico_donnees['path_dest_flow'])
                except Exception as e:
                    msg_erreur=e
                    print("sortie_metashape:erreur:{}::{}/{}:".format("probleme orthomosaique param dem vide",etape_wkf,nb_etape_wkf))
                if not os.path.isfile(path_file_ortho+name_file_ortho):
                    try:
                        chk.raster_transform.formula = ["(B1/32768)", "(B2/32768)", "(B3/32768)","(B4/32768)","(B5/32768)"]
                        chk.raster_transform.false_color = [2, 1, 0]
                        #chk.raster_transform.range=(0,0.5)
                        chk.raster_transform.calibrateRange()
                        proj = Metashape.OrthoProjection()
                        proj.crs = Metashape.CoordinateSystem(dico_config_expe['crs'])
                        if dico_config_expe['param_dem']['Xmin']!=None:
                            chk.exportRaster(path_file_ortho+name_file_ortho,projection=proj,region=region_dem, resolution_x=parametre_dem[1],resolution_y=parametre_dem[1],source_data=Metashape.OrthomosaicData,raster_transform=Metashape.RasterTransformValue,block_width=10000, block_height=10000,split_in_blocks=True,save_alpha=True,progress=progress_print)
                        else:
                            chk.exportRaster(path_file_ortho+name_file_ortho,projection=proj,source_data=Metashape.OrthomosaicData,raster_transform=Metashape.RasterTransformValue,block_width=10000, block_height=10000,split_in_blocks = True,progress=progress_print)

                        #upload_ftp(name_file_ortho,path_file_ortho,ftp_path_racine+dico_donnees['path_dest_flow'].replace('\\','/'))
                        try:
                            path_file_report=os.path.join(dico_donnees['path_dest_local'],dico_donnees['path_dest_flow'])
                            name_file_report='{}_{}_rapport_reflectance.pdf'.format(n_chk[1],dico_donnees['date_donnees'])
                            chk.exportReport(path_file_report+name_file_report)
                            upload_ftp(name_file_report,path_file_report,ftp_path_racine+dico_donnees['path_dest_flow'].replace('\\','/'))
                        except Exception as e:
                            msg_erreur=e
                            print("/r/nsortie_metashape:warning:impossible d'exporter le rapport::{}/{}:/r/n".format(etape_wkf,nb_etape_wkf))
                        #if chk.elevation:
                        #    chk.elevation.clear()
                        doc.save()
                        print('/r/nsortie_metashape:status:Fin:{:.2f}:{}/{}:{:.2f}:/r/n'.format(100,etape_wkf,nb_etape_wkf,getFolderSize(local_dir)/1e9))
                        etape_wkf+=1
                    except Exception as e:
                        msg_erreur=e
                        print("sortie_metashape:erreur:{}::{}/{}:".format("probleme orthomosaique",etape_wkf,nb_etape_wkf))
                else:
                    etape_wkf+=1
                #Chunk RGB
                n_chk=list_chunk[1]
                chk =doc.chunks[n_chk[0]]
                #export markers
                name_file_markers='{}_{}_markers.xml'.format(n_chk[1],dico_donnees['date_donnees'])
                path_file_markers=os.path.join(dico_donnees['path_dest_local'],dico_donnees['path_dest_flow'])
                if not os.path.isfile(path_file_markers+name_file_markers):
                    try:
                        if chk.markers!=[]:
                            chk.exportMarkers(path_file_markers+name_file_markers)
                            upload_ftp(name_file_markers,path_file_markers,ftp_path_racine+dico_donnees['path_dest_flow'].replace('\\','/'))
                    except Exception as e:
                        msg_erreur=e
                        print("/r/nsortie_metashape:warning:impossible d'exporter les markers::{}/{}:/r/n".format(etape_wkf,nb_etape_wkf))
                #export ortho rgb
                name_file_ortho='{}_{}_ortho.tif'.format(n_chk[1],dico_donnees['date_donnees'])
                path_file_ortho=os.path.join(dico_donnees['path_dest_local'],dico_donnees['path_dest_flow'])
                if not os.path.isfile(path_file_ortho+name_file_ortho):
                    try:
                        chk.exportRaster(path_file_ortho+name_file_ortho,region=region_dem, resolution_x=parametre_dem[1],resolution_y=parametre_dem[1],source_data=Metashape.OrthomosaicData,progress=progress_print)
                        upload_ftp(name_file_ortho,path_file_ortho,ftp_path_racine+dico_donnees['path_dest_flow'].replace('\\','/'))
                        try:
                            path_file_report=os.path.join(dico_donnees['path_dest_local'],dico_donnees['path_dest_flow'])
                            name_file_report='{}_{}_rapport.pdf'.format(n_chk[1],dico_donnees['date_donnees'])
                            chk.exportReport(path_file_report+name_file_report)
                            upload_ftp(name_file_report,path_file_report,ftp_path_racine+dico_donnees['path_dest_flow'].replace('\\','/'))
                        except Exception as e:
                            msg_erreur=e
                            print("/r/nsortie_metashape:warning:impossible d'exporter le rapport::{}/{}:/r/n".format(etape_wkf,nb_etape_wkf))
                        doc.save()
                        print('/r/nsortie_metashape:status:Fin:{:.2f}:{}/{}:{:.2f}:/r/n'.format(100,etape_wkf,nb_etape_wkf,getFolderSize(local_dir)/1e9))
                        etape_wkf+=1

                    except Exception as e:
                        msg_erreur=e
                        print("sortie_metashape:erreur:{}::{}/{}:".format("probleme orthomosaique",etape_wkf,nb_etape_wkf))
                else:
                    etape_wkf+=1


    except Exception as e:
        print("sortie_metashape:erreur:{}::{}/{}:".format("probleme general",etape_wkf,nb_etape_wkf))
        msg_erreur=e
        doc.save()
        del doc
    try :
        doc.save()
        del doc
    except :
        pass

    try :
        temps_flow_str=caract_projet[1]
    except:
        temps_flow=time.time()-temps_debut
        temps_flow_str=time.strftime("%Hh %Mm",time.gmtime(temps_flow))
    if msg_erreur!="":
        #print("/r/nsortie_metashape:status:Echec:{}:{}/{}:{:.2f}:{}:{}:{}:{}:{}:/r/n".format(re.sub("\!|\'|\?",msg_erreur),etape_wkf,nb_etape_wkf,getFolderSize(local_dir)/1e9,temps_flow_str,rmse_xyz,erreur_X,erreur_Y,erreur_Z))
        print("/r/nsortie_metashape:status:Echec:{}:{}/{}:{:.2f}:{}:{}:{}:{}:{}:/r/n".format(msg_erreur,etape_wkf,nb_etape_wkf,getFolderSize(local_dir)/1e9,temps_flow_str,rmse_xyz,erreur_X,erreur_Y,erreur_Z))
    else:
        print("/r/nsortie_metashape:status:Fin:100.00:{}/{}:{:.2f}:{}:{}:{}:{}:{}:/r/n".format(etape_wkf,nb_etape_wkf,getFolderSize(local_dir)/1e9,temps_flow_str,rmse_xyz,erreur_X,erreur_Y,erreur_Z))

def main():
    arg='{"id_donnees":1717677883842,"date_donnees":"2024/06/06","date":"06/06/2024 14:44:44","etape":"4/6","status":"value is not a number","color_status":"#ff0000","workflow":"MatchPhotos,Ortho,Export,","progression":null,"nom_op":"EROY","nom_expe":"SOERE","vecteur":"Drone","camera":"Camera_multispectrale","path_dest_nas":"//192.168.0.2/Phenotypage/Data/","path_dest_local":"D:/Data/","path_dest_expe":"SOERE/2024_06_06/","path_dest_donnees":"SOERE/2024_06_06/Drone/Camera_multispectrale/","path_dest_flow":"SOERE/2024_06_06/flow/","size_donnees":120.59,"flag_data_local":"True","time_duration":"00h 00m","rmse_xyz":"NaN","erreur_X":"NaN","erreur_Y":"NaN","erreur_Z":"NaN"}'
    dico_donnees = json.loads('{}'.format(arg))
    photogrammetrie_multispectrale(dico_donnees)
    print("python main function")


if __name__ == '__main__':
    main()
