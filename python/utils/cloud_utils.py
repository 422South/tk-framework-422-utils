import os
from tank_vendor import six
from sgtk.platform.qt import QtCore, QtGui
import zipfile
import hmac
import hashlib
import ast
import sys
import sgtk
from sgtk.util import filesystem

logger = sgtk.platform.get_logger(__name__)

fw = sgtk.platform.get_framework("tk-botoPackages")
if six.PY3:
    package_path = os.path.join(fw.disk_location,  'python3')
else:
    package_path = os.path.join(fw.disk_location, 'python27')

logger.debug("Added path %s" % package_path)
if package_path not in sys.path:
    sys.path.insert(1, package_path)

import boto3
import requests

from .ui.dialog import show_dialog



fileToUploadSize = float(0)
chunkCount = float(0)
loadingDialog = None


def isMachineRemote():
    # Ping deadline to see if the user computer is on our local network
    is_local = os.environ.get('SG_REMOTE', '-1')
    if is_local == "1":
        return True
    else:
        return False
    #
    # response = os.system('ping -n 1 -w 1000 192.168.1.243')
    # if response == 0:
    #     return True
    # else:
    #     return False


def downloadFromCloud(shotgunInstance, context, srcPath, destPath=None):
    # INSTALL PIP AND BOTO
    global loadingDialog
    loadingDialog = show_dialog()
    loadingDialog.updateLabel("Loading prerequisite libraries...")
    logger.info("Loading prerequisite libraries...")
    # Get the S3 access keys
    loadingDialog.updateLabel("Obtaining cloud server login information...")
    loadingDialog.updateProgress(5)
    QtGui.QApplication.processEvents()
    logger.info("Obtaining cloud server login information...")

    key = shotgunInstance.find_one('CustomNonProjectEntity02', [['code', 'is', 'verifyUserKey']], ['sg_key'])['sg_key']
    stringToVerify = six.ensure_str(shotgunInstance.find_one('CustomNonProjectEntity02', [['code', 'is', 'verifyUserKey']], ['description'])['description'])
    dataObj = hmac.new(key, stringToVerify, hashlib.sha1).hexdigest()

    fileNameToDownload = os.path.basename(srcPath)
    infoToLog = context.user['name'] + ' downloaded ' + six.ensure_str(fileNameToDownload) + ' from ' + context.project['name'] + ' from the cloud'
    myObj = {'stringToVerify': dataObj, 'logInfo': infoToLog}
    response = requests.post(url="https://deadline.422south.com/shotgun/getKeys", data=myObj)

    if response.status_code != 200:
        loadingDialog.updateProgress(100)
        loadingDialog.updateLabel("ERROR: Connecting to cloud server")
        logger.info("No response from deadline")
        logger.info(myObj)
        raise Exception("Couldn't get a valid response from deadline")

    logger.info("Received response from deadline...")

    keys = ast.literal_eval(response.text)
    ACCESS_KEY = keys['ACCESS_KEY']
    SECRET_KEY = keys['SECRET_KEY']
    bucketName = '422-south-shotgun'
    client = boto3.client('s3', aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY)

    pubFile = shotgunInstance.find_one('PublishedFile', [['code', 'is', six.ensure_str(fileNameToDownload)]],
                                            ['sg_cloudpublishstatus', 'path_cache', 'id',
                                             'sg_cloudpublishtextures',
                                             'sg_cloudpublishfolderpath', 'path_cache_storage'])

    if pubFile is None or pubFile['sg_cloudpublishstatus'] is None:
        loadingDialog.updateProgress(100)
        loadingDialog.updateLabel("ERROR: File not found on the cloud")
        QtGui.QApplication.processEvents()
        raise Exception('Could not find the file on the cloud')

    filePathMount = pubFile['path_cache_storage']['name']
    localStorage = shotgunInstance.find_one('LocalStorage', [['cached_display_name', 'is', filePathMount]], ['windows_path'])
    filePathBase = localStorage['windows_path']

    orionLocation = os.path.join(filePathBase, pubFile['path_cache'])

    textures = pubFile['sg_cloudpublishtextures']
    amazonKey = pubFile['sg_cloudpublishfolderpath'] + '/' + os.path.basename(orionLocation)

    if not destPath:
        filesystem.ensure_folder_exists(os.path.dirname(orionLocation))
        # Do the download of the maya scene
        try:
            os.makedirs(os.path.dirname(orionLocation))
        except WindowsError:
            pass

    loadingDialog.updateLabel("Downloading your scene file...")
    loadingDialog.updateProgress(10)
    QtGui.QApplication.processEvents()
    logger.info("Downloading your scene file...")

    pathToSceneCloud = os.path.dirname(amazonKey) + '/' + os.path.splitext(os.path.basename(amazonKey))[0] + '.zip'
    pathToSceneOrion = os.path.join(os.path.dirname(orionLocation), os.path.splitext(os.path.basename(orionLocation))[0] + '.zip')
    if destPath:
        pathToSceneOrion = os.path.join(destPath, os.path.basename(pathToSceneOrion))
        try:
            os.makedirs(os.path.dirname(pathToSceneOrion))
        except WindowsError:
            pass

    # Check how big the file to download is
    global fileToUploadSize

    try:
        getFileSize = client.head_object(Bucket=bucketName, Key=pathToSceneCloud)
    except Exception as e:
        raise Exception("Unable to download from Cloud using key - '%s'" % pathToSceneCloud)

    fileToUploadSize = getFileSize['ContentLength']

    try:
        clientResponse = client.download_file(bucketName, pathToSceneCloud, pathToSceneOrion, Callback=_the_call_back)
    except:
        raise Exception("Unable to download from Cloud using key - '%s'" % pathToSceneCloud)

    # Unzip the scene file
    loadingDialog.updateLabel("Unzipping your scene file...")
    loadingDialog.updateProgress(75)
    QtGui.QApplication.processEvents()
    logger.info("Unzipping your scene file...")

    fileToUnzip = pathToSceneOrion
    with zipfile.ZipFile(fileToUnzip, 'r') as zip_ref:
        zip_ref.extractall(os.path.dirname(fileToUnzip))
    os.remove(fileToUnzip)

    # Download all the textures as well
    loadingDialog.updateProgress(85)
    QtGui.QApplication.processEvents()
    count = 1

    if textures is not None:
        texturesDict = ast.literal_eval(textures)
        for textureInfo in texturesDict:
            loadingDialog.updateLabel(
                "Downloading texture " + six.ensure_str(count) + " of " + six.ensure_str(len(texturesDict)) + " from cloud...")
            QtGui.QApplication.processEvents()
            logger.info("Downloading texture " + six.ensure_str(count) + " of " + six.ensure_str(len(texturesDict)) + " from cloud...")

            texturePath = os.path.join(filePathBase, textureInfo[0])
            if not destPath:
                try:
                    os.makedirs(os.path.dirname(texturePath))
                except WindowsError:
                    pass

            pathToTextureCloud = os.path.dirname(pubFile['sg_cloudpublishfolderpath']) + '/' + \
                                 os.path.splitext(os.path.basename(textureInfo[1]))[0] + '.zip'
            pathToTextureOrion = os.path.join(os.path.dirname(texturePath),
                                              os.path.splitext(os.path.basename(texturePath))[0] + '.zip')
            if destPath:
                pathToTextureOrion = os.path.join(destPath, 'images', os.path.basename(pathToTextureOrion))
                try:
                    os.makedirs(os.path.dirname(pathToTextureOrion))
                except WindowsError:
                    pass

            try:
                response = client.download_file(bucketName, pathToTextureCloud, pathToTextureOrion)
            except:
                raise Exception("Unable to download texture file from Cloud using key - '%s'" % pathToTextureCloud)

            # Unzip the files
            textureToUnzip = pathToTextureOrion
            with zipfile.ZipFile(textureToUnzip, 'r') as zip_ref:
                zip_ref.extractall(os.path.dirname(textureToUnzip))
            os.remove(textureToUnzip)

            count += 1

    # Update this field to CloudOrion, only if they're on a local machine
    # If they're not local, dont change this field because the file isn't being put on Orion
    machineRemote = isMachineRemote()

    if not machineRemote:
        updatedVerData = {
            'sg_cloudpublishstatus': 'RemoteSynced',
        }
        shotgunInstance.update('PublishedFile', pubFile['id'], updatedVerData)

    loadingDialog.updateLabel("Cloud download finished")
    loadingDialog.updateProgress(100)
    QtGui.QApplication.processEvents()
    logger.info("Cloud download finished")

    loadingDialog.closeUI()


def _the_call_back(chunk):
    global chunkCount
    global fileToUploadSize
    global loadingDialog

    chunkCount += chunk

    progressPercent = int(round((chunkCount / fileToUploadSize) * 100, 0))

    # this is to account for the fact that progress is already at 10 percent
    # when we get here and ends at 90 when we finish here 75-10=65
    progressPercent = (progressPercent * 0.65) + 10

    loadingDialog.updateProgress(int(progressPercent))
    QtGui.QApplication.processEvents()