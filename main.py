## Instalações para uso no google colab
# !apt-get install -qq libgdal-dev libproj-dev
# !pip install --no-binary shapely shapely --force
# !pip install cartopy
# !pip install metpy
# !pip install s3fs
# !pip install matplotlib==3.1.1

## Importação de bibliotecas
from datetime import datetime
from dateutil.relativedelta import relativedelta
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.pyplot as plt
import metpy  # noqa: F401
import numpy as np
import xarray
import s3fs
import math
from scipy import signal
from PIL import Image
from numpy import *
from pylab import *
import cv2
import random

## Funções
def contrast_correction(color, contrast):
    """
    Modifica o contraste de um RGB
    https://www.dfstudios.co.uk/articles/programming/image-programming-algorithms/image-processing-algorithms-part-5-contrast-adjustment/

    Input:
        color    - array representando os canais RGB
        contrast - nível de correção de contraste
    """
    C = (259*(contrast + 255))/(255.*259-contrast)
    COLOR = C*(color-.5)+.5
    COLOR = np.clip(COLOR, 0, 1)
    return COLOR

def plota_goes(dia, hora, minuto):
    """
    Realiza busca, download, e plotagem de imagem True Color
    do satélite GOES-16 para a América do Sul
    dia: string no formato 'YYYY-mm-dd'
    hora: int no formato 'hh', horário de Brasília
    minuto: int no formato 'mm'
    """

    # Parâmetros de busca
    data = datetime.datetime.strptime(dia, '%Y-%m-%d')
    num_dia = str(data.timetuple().tm_yday)
    if len(num_dia) == 1:
      num_dia = '00' + num_dia
    elif len(num_dia) == 2:
      num_dia = '0' + num_dia
    hora = str(hora+3)
    if len(hora) < 2:
      hora = '0' + hora

    # Download de arquivos (Brian Blaylock)
    ## Credenciais anônimas para acesso a dados públicos
    fs = s3fs.S3FileSystem(anon=True)

    ## Lista GOES-16
    fs.ls('s3://noaa-goes16/')

    ## Lista de arquivos dentro da hora determinada
    files = np.array(fs.ls(f'noaa-goes16/ABI-L2-MCMIPF/2022/{num_dia}/{hora}'))
    print('Arquivos disponíveis:')
    print(files)

    ## Download do arquivo NetCDF
    try:
      if minuto < 10:
        fs.get(files[0], files[0].split('/')[-1])
        file_name = files[0].split('/')[-1]
      elif minuto < 20:
        fs.get(files[1], files[1].split('/')[-1])
        file_name = files[1].split('/')[-1]
      elif minuto < 30:
        fs.get(files[2], files[2].split('/')[-1])
        file_name = files[2].split('/')[-1]
      elif minuto < 40:
        fs.get(files[3], files[3].split('/')[-1])
        file_name = files[3].split('/')[-1]
      elif minuto < 50:
        fs.get(files[4], files[4].split('/')[-1])
        file_name = files[4].split('/')[-1]
      else:
        fs.get(files[5], files[5].split('/')[-1])
        file_name = files[5].split('/')[-1]
    except:
      print('Data ou hora não disponível.')

    minuto = str(minuto)
    if len(minuto) < 2:
      minuto = '0' + minuto

    # Abrindo imagem
    imagem = path+file_name
    F = xarray.open_dataset(imagem)

    ## Carregando arrays RGB
    R = F['CMI_C02'][:].data
    G = F['CMI_C03'][:].data
    B = F['CMI_C01'][:].data

    ## Valores RGB precisam ficar entre 0 e 1
    R = np.clip(R, 0, 1)
    G = np.clip(G, 0, 1)
    B = np.clip(B, 0, 1)

    ## Aplicando correção gamma
    gamma = 2.2
    R = np.power(R, 1/gamma)
    G = np.power(G, 1/gamma)
    B = np.power(B, 1/gamma)

    ## Calculando verde verdadeiro
    G_true = 0.48358168 * R + 0.45706946 * B + 0.06038137 * G
    G_true = np.clip(G_true, 0, 1)

    ## Array RGB final
    RGB = np.dstack([R, G_true, B])

    ## Usamos a variável 'CMI_C02' para obter os metadados
    dat = F.metpy.parse_cf('CMI_C02')

    x = dat.x
    y = dat.y


    # Data e hora da imagem
    ## Hora de início do imageamento
    scan_start = datetime.datetime.strptime(F.time_coverage_start, '%Y-%m-%dT%H:%M:%S.%fZ')
    scan_start_bra = scan_start - relativedelta(hours=3)

    ## Hora de fim do imageamento
    scan_end = datetime.datetime.strptime(F.time_coverage_end, '%Y-%m-%dT%H:%M:%S.%fZ')
    scan_end_bra = scan_end - relativedelta(hours=3)

    ## Hora de criação do arquivo
    file_created = datetime.datetime.strptime(F.date_created, '%Y-%m-%dT%H:%M:%S.%fZ')

    ## O 't' é o ponto médio do imageamento
    midpoint = str(F['t'].data)[:-8]
    scan_mid = datetime.datetime.strptime(midpoint, '%Y-%m-%dT%H:%M:%S.%f')

    print('Scan Start    : {}'.format(scan_start))
    print('Scan midpoint : {}'.format(scan_mid))
    print('Scan End      : {}'.format(scan_end))
    print('File Created  : {}'.format(file_created))
    print('Scan Duration : {:.2f} minutes'.format((scan_end-scan_start).seconds/60))


    # Aplicando normalização para visualização de nuvens em períodos noturnos 
    # IR Channel
    cleanIR = F['CMI_C13'].data

    # Normalize the channel between a range.
    #       cleanIR = (cleanIR-minimumValue)/(maximumValue-minimumValue)
    cleanIR = (cleanIR-90)/(313-90)

    # Apply range limits to make sure values are between 0 and 1
    cleanIR = np.clip(cleanIR, 0, 1)

    # Invert colors so that cold clouds are white
    cleanIR = 1 - cleanIR

    # Lessen the brightness of the coldest clouds so they don't appear so bright
    # when we overlay it on the true color image.
    cleanIR = cleanIR/1.4

    # Yes, we still need 3 channels as RGB values. This will be a grey image.
    RGB_cleanIR = np.dstack([cleanIR, cleanIR, cleanIR])


    # Aplicando contraste
    ## Amount of contrast
    contrast_amount = 105

    ## Apply contrast correction
    RGB_contrast = contrast_correction(RGB, contrast_amount)

    ## Add in clean IR to the contrast-corrected True Color image
    RGB_contrast_IR = np.dstack([np.maximum(RGB_contrast[:, :, 0], cleanIR),
                                np.maximum(RGB_contrast[:, :, 1], cleanIR),
                                np.maximum(RGB_contrast[:, :, 2], cleanIR)])
    

    # Projeção geoestacionária
    ## We'll use the `CMI_C02` variable as a 'hook' to get the CF metadata.
    dat = F.metpy.parse_cf('CMI_C02')
    geos = dat.metpy.cartopy_crs

    ## We also need the x (north/south) and y (east/west) axis sweep of the ABI data
    x = dat.x
    y = dat.y


    # PLOTAGEM
    # Determinando tamanho da figura
    fig = plt.figure(figsize=(20, 16))

    # set the map domain
    domain = [-90.0,-30.0,-60.0,15.0] #lon W, lon E, lat S, lat N

    # calculates the central longitude of the plot
    lon_cen = 360.0+(domain[0]+domain[1])/2.0

    # Create axis with Geostationary projection
    ax = fig.add_axes([0.1, 0.16, 0.80, 0.75], projection=ccrs.PlateCarree(lon_cen))

    ax.set_extent([domain[0]+360.0, domain[1]+360.0, domain[2], domain[3]],
                  crs=ccrs.PlateCarree())

    # Add the RGB image to the figure. The data is in the same projection as the axis we just created.
    ax.imshow(RGB_contrast_IR, transform=geos)

    # # Add Coastlines and States
    ax.coastlines(resolution='110m', color='gold', linewidth=0.25)
    ax.add_feature(ccrs.cartopy.feature.NaturalEarthFeature(
            category='cultural',
            name='admin_1_states_provinces_lines',
            scale='50m',
            facecolor='none',
            edgecolor='gold'), linewidth=0.25)
    ax.add_feature(ccrs.cartopy.feature.BORDERS, linewidth=0.25, edgecolor='gold')

    # Salvando plot
    plt.axis('off')
    plt.savefig(f'{path}GOES16_{dia}_{hora}_{minuto}.png', bbox_inches='tight', dpi=500)
    plt.show()
    plt.close()

## Algoritmo Lucas-Kanade
def LK_OpticalFlow(Image1, Image2):
    '''
    Aplicação do algoritmo Lucas-Kanade.
    Autor: khushboo_agarwal (https://github.com/khushboo-agarwal/Optical-Flow)
    '''
    I1 = np.array(Image1)
    I2 = np.array(Image2)
    S = np.shape(I1)

    # Applying Gaussian filter of size 3x3 to eliminate any noise
    I1_smooth = cv2.GaussianBlur(I1 #input image
                  ,(3,3)	#shape of the kernel
                  ,0      #lambda
                  )
    I2_smooth = cv2.GaussianBlur(I2, (3,3), 0)

    '''
    let the filter in x-direction be Gx = 0.25*[[-1,1],[-1,1]]
    let the filter in y-direction be Gy = 0.25*[[-1,-1],[1,1]]
    let the filter in xy-direction be Gt = 0.25*[[1,1],[1, 1]]
    **1/4 = 0.25** for a 2x2 filter
    '''
      
    # First Derivative in X direction
    Ix = signal.convolve2d(I1_smooth,[[-0.25,0.25],[-0.25,0.25]],'same') + signal.convolve2d(I2_smooth,[[-0.25,0.25],[-0.25,0.25]],'same')
    # First Derivative in Y direction
    Iy = signal.convolve2d(I1_smooth,[[-0.25,-0.25],[0.25,0.25]],'same') + signal.convolve2d(I2_smooth,[[-0.25,-0.25],[0.25,0.25]],'same')
    # First Derivative in XY direction
    It = signal.convolve2d(I1_smooth,[[0.25,0.25],[0.25,0.25]],'same') + signal.convolve2d(I2_smooth,[[-0.25,-0.25],[-0.25,-0.25]],'same')
    
    # Finding the good features
    features = cv2.goodFeaturesToTrack(I1_smooth # Input image
    ,10000 # max corners
    ,0.01 # lambda 1 (quality)
    ,10 # lambda 2 (quality)
    )	

    feature = np.int0(features)
    
    # Creating the u and v vector
    u = v = np.nan*np.ones(S)
    
    # Calculating the u and v arrays for the good features obtained n the previous step.
    for l in feature:
      j,i = l.ravel()
      # calculating the derivatives for the neighbouring pixels
      # since we are using  a 3*3 window, we have 9 elements for each derivative.
      
      IX = ([Ix[i-1,j-1],Ix[i,j-1],Ix[i-1,j-1],Ix[i-1,j],Ix[i,j],Ix[i+1,j],Ix[i-1,j+1],Ix[i,j+1],Ix[i+1,j-1]]) #The x-component of the gradient vector
      IY = ([Iy[i-1,j-1],Iy[i,j-1],Iy[i-1,j-1],Iy[i-1,j],Iy[i,j],Iy[i+1,j],Iy[i-1,j+1],Iy[i,j+1],Iy[i+1,j-1]]) #The Y-component of the gradient vector
      IT = ([It[i-1,j-1],It[i,j-1],It[i-1,j-1],It[i-1,j],It[i,j],It[i+1,j],It[i-1,j+1],It[i,j+1],It[i+1,j-1]]) #The XY-component of the gradient vector
      
      # Using the minimum least squares solution approach
      LK = (IX, IY)
      LK = np.matrix(LK)
      LK_T = np.array(np.matrix(LK)) # transpose of A
      LK = np.array(np.matrix.transpose(LK)) 
      
      A1 = np.dot(LK_T,LK) #Psedudo Inverse
      A2 = np.linalg.pinv(A1)
      A3 = np.dot(A2,LK_T)
      
      (u[i,j],v[i,j]) = np.dot(A3,IT) # we have the vectors with minimized square error
    
    #======= Plotting the vectors on the image========
    plt.figure(figsize=(20, 16), frameon=False)
    plt.imshow(I1,cmap=cm.gray)
    plt.axis('off')
    for i in range(S[0]):
      for j in range(S[1]):
        if abs(u[i,j])>t or abs(v[i,j])>t: # setting the threshold to plot the vectors
          plt.arrow(j,i,v[i,j],u[i,j],head_width = 4, head_length = 3, color = 'red')

    # Exportando imagem
    plt.savefig(f'GOES16_vetores_{data0}{hora0}{minuto0}_a_{data1}{hora1}{minuto1}.png', bbox_inches='tight', dpi=500)      
    plt.show()

## Função principal
def goes16_motion_vectors(path, data0, hora0, minuto0, data1, hora1, minuto1):
    '''
    Supondo que o usuário queira visualizar o vetor de deslocamento de nuvens entre as 14:00 e as 14:30 do dia 01 de Junho de 2022, inserir os dados como se segue:

    path: string da pasta onde serão salvos os arquivos de imagem exportados (exemplo: 'D:\Documentos\goes16_motion_vectors\')

    data0: string de data no formato 'YYYY-mm-dd' (exemplo: '2022-06-01') 
    hora0: int de hora no formato hh (exemplo: 14)
    minuto0: int de minuto no formato mm (exemplo: 00)

    data1: idem data0 (exemplo: '2022-06-01')
    hora1: idem hora0 (exemplo: 14)
    minuto1: idem minuto0 (exemplo: 30)

    retorna: imagem no tempo 0, imagem no tempo 1 e imagem no tempo 1 com os vetores de deslocamento relativos entre o tempo 0 e o tempo 1
    '''
    
    # Plotagem e exportação das imagens no tempo 0 e no tempo 1
    plota_goes(data0, hora0, minuto0)
    plota_goes(data1, hora1, minuto1)

    # Limiar
    t = 0.3
    
    # Abrindo as imagens exportadas
    Image1 = Image.open(f'{path}GOES16_{data0}_{str(hora0)}_{str(minuto0).png').convert('L')
    Image2 = Image.open(f'{path}GOES16_{data1}_{str(hora1)}_{str(minuto1).png').convert('L')
    
    LK_OpticalFlow(Image1, Image2)
