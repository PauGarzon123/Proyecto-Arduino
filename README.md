<p align="center">
  <a href="https://github.com/PauGarzon123/Proyecto-Arduino/graphs/contributors">
    <img src="https://img.shields.io/badge/Contribuyentes-3-blue?style=for-the-badge&logo=github" alt="Contribuyentes">
  </a>
</p>

# Proyecto‑Simulación satelital

## Descripción  
Proyecto basado en Arduino que simula un sistema satelital formado principalmete por 2 partes:  
-Un satelite simulado  
-Una estación tierra

En el proyecto el satelite se encarga de recoger datos como la humedad, distancia o temperatura.  
Este los envia a la estación tierra donde los muestra al usuario mediante una interfaz grafica.

Esta interfaz ademas permite hacer cambios en la toma de datos como por ejemplo un cambio de direccion en el radar.
Este cambio se transmite de tierra al satélite para que pueda realizar el cambio.

## Herramientas  
### Lenguajes
[![Static Badge](https://img.shields.io/badge/python-py-yellow?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)  
![Lenguaje](https://img.shields.io/badge/C-C-darkblue?style=for-the-badge&logo=c%2B%2B)  
### Hardware y librerias
[![Static Badge](https://img.shields.io/badge/arduino-ino-blue?style=for-the-badge&logo=arduino&logoColor=white)](https://www.arduino.cc/en/software/)  
[![Static Badge](https://img.shields.io/badge/Numpy-skyblue?style=for-the-badge)](https://numpy.org/)  
[![Static Badge](https://img.shields.io/badge/Matplotlib-skyblue?style=for-the-badge)](http://matplotlib.org/)  
[![Static Badge](https://img.shields.io/badge/Pillow-skyblue?style=for-the-badge)](https://pypi.org/project/pillow/)  
[![Static Badge](https://img.shields.io/badge/Serial-skyblue?style=for-the-badge)](https://pyserial.readthedocs.io/)  
[![Static Badge](https://img.shields.io/badge/pygame-skyblue?style=for-the-badge)](https://www.pygame.org/news)  
![Static Badge](https://img.shields.io/badge/ArduCAM-skyblue?style=for-the-badge)  
![Static Badge](https://img.shields.io/badge/DHTsensor-skyblue?style=for-the-badge)  



##  Instalación
### 1. Instalación de Visual Studio Code y el lenguaje C  
   [Ver video](https://www.youtube.com/watch?v=qQT-6WufAEE)
### 2. Instalación de Python  
   [Ver video](https://www.youtube.com/watch?v=HJErA1k95k8)
### 3.Instalación Arduino IDE  
  [Página oficial de Arduino](https://www.arduino.cc/en/software)
   
### 4. Clonar el repositorio
```bash
git clone https://github.com/PauGarzon123/Proyecto-Arduino.git
cd Proyecto-Arduino
```
### 5. Instalar librerías de Arduino
1. Abrir Arduino IDE.
2. Ir a **Sketch → Include Library → Manage Libraries…**
3. Buscar e instalar las siguientes librerías:
   - `DHT sensor library` (Adafruit)
   - `ArduCAM` (ArduCAM)
### 6. Instalar pip 
1. Descargar el script [get-pip.py](https://bootstrap.pypa.io/get-pip.py)
2. Abrir CMD y ejecutar:
```cmd
python get-pip.py
```

### 7.Instalar librerías de Python
Abrir la terminal o CMD y instalar las librerías mencionadas en las herramientas con el pip.

### 8.Montar el circuito  




## Videos del proyecto
1. **Versión 1** – Demostración básica del satélite y estación  
   [Ver video](https://drive.google.com/file/d/1Z6En6WkZa4Dj-eJ62Kv3MVlINoD3yJOS/view?usp=sharing)
2. **Versión 2** – Interacción avanzada con la interfaz gráfica  
   [Ver video](https://drive.google.com/file/d/1hKNK0I4ORd2DQYQc4liZ1lFfx9cRLFUs/view?usp=sharing)
3. **Versión 3** – Integración completa del satélite y estación  
   [Ver video](https://drive.google.com/file/d/1fx8jCaYvltBJq02DE8GkxMYV_DyTs3j7/view?usp=sharing)

