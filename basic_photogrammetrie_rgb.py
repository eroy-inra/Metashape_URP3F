'''
Created Date: Thursday, November 21st 2024, 2:22:52 pm
Author: EROY

Copyright (c) 2024 INRAE-URP3F
'''
import Metashape,os
Metashape.app.cpu_enable=True

#Selectionner le numero d'etape a realiser (
#   1 = creation du projet et alignement des cameras
#   2 = creation du nuage de points dense, mnt et orthomosaic
#
#   Après l'etape 1, ouvrez le projet psx et placer les reperes manuellement.
#   Puis lancer l'etape 2.
etape=1 

project_name="SFM-test-RGB"                     #Nom du projet
project_path="D:\\Basic_sfm\\"                  #chemin du projet
photos_path="D:\\Basic_sfm\\photos\\"           #chemin des photos
project_crs="EPSG::2154"                        #Systeme de coordonnes du projet
gcp_name="SFM-test-RGB_gcp.csv"                 #Nom du fichier de repere georeferences
license_metashape_file="License_metashape.txt"  #Nom du fichier de licence
project_name_psx=os.path.join(project_path,'{}.psx'.format(project_name))

#Lecture de la license de Metashape
file = open(os.path.join(project_path,license_metashape_file), "r")
license_metashape = file.read()
print(license_metashape)
file.close()
if not Metashape.license.valid:
    Metashape.license.activate(license_metashape) # replace xxxx by your Activation key

##############################################################################################
if etape==1:

    #Création du projet
    doc  = Metashape.Document()
    doc.save(project_name_psx)

    #Création du chunck si absent
    chk =doc.chunk
    if not chk:
        chk =doc.addChunk()
    chk.label=project_name

    #Liste les photos a inserer
    liste_fichier_brute=os.listdir(photos_path)
    list_file_image=[]
    for h in liste_fichier_brute:
        if os.path.isdir(os.path.join(photos_path,h))==True:
            #print (os.path.join(dico_donnees['path_dest_donnees'],h))
            for f in os.listdir(os.path.join(photos_path,h)):
                if f[-4:]==".JPG" :
                    list_file_image.append(os.path.join(photos_path,h,f))
        else:
            if h[-4:]==".JPG" :
                list_file_image.append(os.path.join(photos_path,h))
    print ("sortie_metashape: Nombre d'image a traiter : {}".format(len(list_file_image)))

    #Import des photos
    chk.addPhotos(list_file_image[:],load_xmp_accuracy=True)
    doc.save()

    #Definit le crs du projet en wgs84
    chk.crs = Metashape.CoordinateSystem("EPSG::4326")

    #Convertit le crs des cameras de wgs84 en lambert 93 puis decoche les references cameras
    crs_lbt93 = Metashape.CoordinateSystem(project_crs)
    for cam in chk.cameras:
        if cam.reference.location:
            cam.reference.location=crs_lbt93.project(chk.crs.unproject(cam.reference.location))
        cam.reference.enabled=False

    #Change le crs du projet en lambert 93
    chk.crs = Metashape.CoordinateSystem(project_crs)

    #Import des points de references (GCP)
    chk.importReference(os.path.join(project_path,gcp_name), Metashape.ReferenceFormat.ReferenceFormatCSV ,    \
                            columns="noyxz", \
                            delimiter=",",    \
                            group_delimiters=False, skip_rows=1,   \
                            items=Metashape.ReferenceItems.ReferenceItemsMarkers,   \
                            crs=Metashape.CoordinateSystem(project_crs), \
                            ignore_labels=False, create_markers=True)
    doc.save()

    #Aligne les cameras (0: Highest, 1: High, 2: Medium, 3: Low, 4: Lowest)
    #Faire plusieurs fois si besoin lorsqu'il n'arrive pas a aligner toutes les photos en 1 fois
    chk.matchPhotos(downscale=1, generic_preselection=True,reference_preselection=False,    \
                    keypoint_limit=40000, tiepoint_limit=4000)
    chk.alignCameras(reset_alignment=True)
    doc.save()
    chk.matchPhotos(downscale=1, generic_preselection=True,reference_preselection=False,    \
                    keypoint_limit=40000, tiepoint_limit=4000)
    chk.alignCameras(reset_alignment=False)
    doc.save()
    chk.matchPhotos(downscale=1, generic_preselection=True,reference_preselection=False,    \
                    keypoint_limit=40000, tiepoint_limit=4000)
    chk.alignCameras(reset_alignment=False)
    doc.save()


##############################################################################################
#   Placer manuellement les reperes sur les photos(environ 4 photos/repere)
#   Dans Metashape, ouvrer les photos, faire cilck droit ajouter repere, et choisir 
#   le numero du repere correspondant
##############################################################################################
elif etape==2:
    doc  = Metashape.Document()
    if os.path.isfile(project_name_psx):
        doc.open(project_name_psx)

    chk =doc.chunk
    #Optimise le positionnements des cameras après avoir positionner les gcp sur les photos
    chk.updateTransform()
    chk.optimizeCameras()
    chk.resetRegion()

    #Creation du nuage dense (1: Highest, 2: High, 3: Medium, 4: Low, 5: Lowest)
    if not chk.dense_cloud:
        if chk.elevation:
            chk.elevation.clear()

        if not chk.depth_maps :
            chk.buildDepthMaps(downscale=2, filter_mode=Metashape.NoFiltering)
            doc.save()
        chk.buildDenseCloud(point_colors=True, point_confidence=True,keep_depth=True, max_neighbors=100)
        doc.save()

    #Creation du modele numerique d'elevation (mne)
    if not chk.elevation:
        chk.buildDem(source_data=Metashape.DenseCloudData,interpolation=Metashape.EnabledInterpolation)
        doc.save()
        chk.exportRaster(os.path.join(project_path,'{}_mne.tif'.format(project_name)),source_data=Metashape.ElevationData)

    #Creation de l'ortomosaique
    if not chk.orthomosaic:
        chk.buildOrthomosaic(surface_data=Metashape.ElevationData, blending_mode=Metashape.MosaicBlending,fill_holes=True)
        doc.save()
        chk.orthomosaic.removeOrthophotos()
        doc.save()
        chk.exportRaster(os.path.join(project_path,'{}_ortho.tif'.format(project_name)),source_data=Metashape.OrthomosaicData)
    
    # Creation du rapport de traitement
    chk.exportReport(os.path.join(project_path,'{}_rapport.pdf'.format(project_name)))

    # Export des markers
    chk.exportMarkers(os.path.join(project_path,'{}_markers.xml'.format(project_name)))


#Fin du traitement
doc.save()
del doc