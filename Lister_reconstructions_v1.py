
def lister_caract_projet_psx(file_projet_psx):
    import Metashape,datetime,os,time
    import numpy as np


    def list_camera_chunk(chunk):
        camera_list = list()
        enabled_list = list()
        align_list = list()


        for camera in chunk.cameras:
            camera_list.append(camera.label)
            if camera.enabled:
                enabled_list.append(camera)
                #print(camera.label + " is enabled.")
                #print ( camera.sensor.location)
            if camera.transform:
                align_list.append(camera)
        return camera_list,enabled_list,align_list


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


    if os.path.isfile(file_projet_psx):
        doc  = Metashape.Document()
        doc.open(file_projet_psx)

    path_doc=doc.path
    list_path=path_doc.split("/")
    path_doc="\\".join(list_path[:-1])
    name_file_projet_psx=list_path[-1]
    expe=doc.chunk.label
    chk=doc.chunk

    resultat_dico={}

    try :
        resultat_dico['Projet/Expe']=expe
        resultat_dico['Projet/path_doc']=path_doc
        resultat_dico['Projet/name_file_projet_psx']=name_file_projet_psx


        if os.path.isfile(os.path.join(path_doc,name_file_projet_psx[:-4]+"_markers.xml" )):
            resultat_dico['Projet/file_markers']=name_file_projet_psx[:-4]+"_markers.xml"
        if os.path.isfile(os.path.join(path_doc,name_file_projet_psx[:-4]+"_mnt.tif" )):
            resultat_dico['Projet/file_mnt']=name_file_projet_psx[:-4]+"_mnt.tif"
        if os.path.isfile(os.path.join(path_doc,name_file_projet_psx[:-4]+"_ortho.tif" )):
            resultat_dico['Projet/file_ortho']=name_file_projet_psx[:-4]+"_ortho.tif"
    except :
        pass

    try :
        resultat_dico['Projet/duration']=time.strftime("%Hh %Mm",time.gmtime(float(chk.point_cloud.meta['MatchPhotos/duration'])+   \
                        float(chk.depth_maps.meta['BuildDepthMaps/duration'])+float(chk.dense_cloud.meta['BuildDenseCloud/duration'])+float(chk.elevation.meta['BuildDem/duration'])))
    except :
        resultat_dico['Projet/duration']="00h 00m"

    try :
        cam,cam_en,cam_align=list_camera_chunk(chk)
        resultat_dico['MatchPhotos/nb_cam']=len(cam)
        resultat_dico['MatchPhotos/nb_cam_act']=len(cam_en)
        resultat_dico['MatchPhotos/nb_cam_align']=len(cam_align)
        resultat_dico['MatchPhotos/OriginalDateTime']=datetime.datetime.strptime(chk.point_cloud.meta['Info/OriginalDateTime'], "%Y:%m:%d %H:%M:%S").strftime("%Y/%m/%d %H:%M:%S")
        resultat_dico['MatchPhotos/LastSavedDateTime']=datetime.datetime.strptime(chk.point_cloud.meta['Info/LastSavedDateTime'], "%Y:%m:%d %H:%M:%S").strftime("%Y/%m/%d %H:%M:%S")
    except :
        pass

    try :
        resultat_dico['MatchPhotos/downscale']=chk.point_cloud.meta['MatchPhotos/downscale']
        resultat_dico['MatchPhotos/duration(s)']=time.strftime("%Hh %Mm",time.gmtime(float(chk.point_cloud.meta['MatchPhotos/duration'])))
        resultat_dico['MatchPhotos/point_count']=len(chk.point_cloud.tracks)
    except :
        pass

    try :
        resultat_dico['BuildDepthMaps/OriginalDateTime']=datetime.datetime.strptime(chk.depth_maps.meta['Info/OriginalDateTime'], "%Y:%m:%d %H:%M:%S").strftime("%Y/%m/%d %H:%M:%S")
        resultat_dico['BuildDepthMaps/LastSavedDateTime']=datetime.datetime.strptime(chk.depth_maps.meta['Info/LastSavedDateTime'], "%Y:%m:%d %H:%M:%S").strftime("%Y/%m/%d %H:%M:%S")
        resultat_dico['BuildDepthMaps/downscale']=chk.depth_maps.meta['BuildDepthMaps/downscale']
        resultat_dico['BuildDepthMaps/duration']=time.strftime("%Hh %Mm",time.gmtime(float(chk.depth_maps.meta['BuildDepthMaps/duration'])))
    except :
        pass

    try :
        resultat_dico['BuildDenseCloud/point_count']=chk.dense_cloud.point_count
        resultat_dico['BuildDenseCloud/duration']=time.strftime("%Hh %Mm",time.gmtime(float(chk.dense_cloud.meta['BuildDenseCloud/duration'])))
    except :
        pass

    try :
        resultat_dico['BuildDem/OriginalDateTime']=datetime.datetime.strptime(chk.elevation.meta['Info/OriginalDateTime'], "%Y:%m:%d %H:%M:%S").strftime("%Y/%m/%d %H:%M:%S")
        resultat_dico['BuildDem/LastSavedDateTime']=datetime.datetime.strptime(chk.elevation.meta['Info/LastSavedDateTime'], "%Y:%m:%d %H:%M:%S").strftime("%Y/%m/%d %H:%M:%S")
        resultat_dico['BuildDem/resolution']=chk.elevation.resolution
        resultat_dico['BuildDem/width']=chk.elevation.width
        resultat_dico['BuildDem/height']=chk.elevation.height
    except :
        pass

    try :
        resultat_dico['BuildOrthomosaic/OriginalDateTime']=datetime.datetime.strptime(chk.orthomosaic.meta['Info/OriginalDateTime'], "%Y:%m:%d %H:%M:%S").strftime("%Y/%m/%d %H:%M:%S")
        resultat_dico['BuildOrthomosaic/LastSavedDateTime']=datetime.datetime.strptime(chk.orthomosaic.meta['Info/LastSavedDateTime'], "%Y:%m:%d %H:%M:%S").strftime("%Y/%m/%d %H:%M:%S")
        resultat_dico['BuildOrthomosaic/resolution']=chk.orthomosaic.resolution
        resultat_dico['BuildOrthomosaic/width']=chk.orthomosaic.width
        resultat_dico['BuildOrthomosaic/height']=chk.orthomosaic.height
    except :
        pass

    try :
        markers_errors=calcul_erreur_marker(doc)
        array_markers=np.array(markers_errors)
        resultat_dico['Projections/nb_markers']=np.size(array_markers[:,0])
        resultat_dico['Projections/Xmin']=np.min(array_markers[:,0])
        resultat_dico['Projections/Xmax']=np.max(array_markers[:,0])
        resultat_dico['Projections/Ymin']=np.min(array_markers[:,1])
        resultat_dico['Projections/Ymax']=np.max(array_markers[:,1])
        resultat_dico['Projections/Zmin']=np.min(array_markers[:,2])
        resultat_dico['Projections/Zmax']=np.max(array_markers[:,2])
        resultat_dico['Projections/Xrmse']=np.sqrt(np.mean(array_markers[:,0]**2))
        resultat_dico['Projections/Yrmse']=np.sqrt(np.mean(array_markers[:,1]**2))
        resultat_dico['Projections/Zrmse']=np.sqrt(np.mean(array_markers[:,2]**2))
        resultat_dico['Projections/XYrmse']=np.sqrt(np.mean(array_markers[:,0]**2+array_markers[:,1]**2))
        resultat_dico['Projections/XYZrmse']=np.sqrt(np.mean(array_markers[:,0]**2+array_markers[:,1]**2+array_markers[:,2]**2))
    except :
        pass

    del doc,chk
    return [resultat_dico,resultat_dico['Projet/duration']]
##print(lister_caract_projet_psx('I:\\test\\Archiduo\\2021_07_21\\flow\\Archiduo_2021_07_21.psx'))