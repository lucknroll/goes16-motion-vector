# goes16-motion-vector
Retorna figura com os vetores de deslocamento de nuvens entre um tempo 0 e um tempo 1 através da função goes16_motion_vectors, baseada em imagens do satélite GOES 16.

Usa matplotlib versão 3.1.1

## Instruções
Supondo que o usuário queira visualizar o vetor de deslocamento de nuvens entre as 14:00 e as 14:30 do dia 01 de Junho de 2022, por exemplo, ele deve utilizar a função principal **goes16_motion_vectors(path, data0, hora0, minuto0, data1, hora1, minuto1)** com os seguintes parâmetros:
    
    path: string da pasta onde serão salvos os arquivos de imagem exportados (exemplo: 'D:\Documentos\goes16_motion_vectors\')
    
    data0: string de data no formato 'YYYY-mm-dd' (exemplo: '2022-06-01') 
    hora0: int de hora no formato hh (exemplo: 14)
    minuto0: int de minuto no formato mm (exemplo: 00)
    
    data1: idem data0 (exemplo: '2022-06-01')
    hora1: idem hora0 (exemplo: 14)
    minuto1: idem minuto0 (exemplo: 30)

A função vai salvar na pasta especificada uma imagem no tempo 0, uma imagem no tempo 1 e um imagem no tempo 1 com os vetores de deslocamento relativos entre o tempo 0 e o tempo 1.


### Resultados
Imagem no tempo 0 (2022-06-01 14:00:00):
![image](https://user-images.githubusercontent.com/102811643/211917820-48fd8678-a475-40c7-925f-109acd5db5c8.png)

Imagem no tempo 1 (2022-06-01 14:30:00):
![image](https://user-images.githubusercontent.com/102811643/211918025-2d1a0ab7-7cf2-4980-a6f0-d12a703fdcb5.png)

Imagem com vetores indicando o deslocamento relativo de nuvens entre o tempo 0 e o tempo 1:
![image](https://user-images.githubusercontent.com/102811643/211918879-5a167cf5-4a9f-4c96-9a46-ae9895bc5cc2.png)
