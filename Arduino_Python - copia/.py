import matplotlib.pyplot as plt
import random
temp = random.randint(25, 30)  # Valor entero entre 25 , 30 (incluidos)
j = 0
plt.ion()
fig, ax = plt.subplots()
linea, = ax.plot([], [], 'y-')  # crea una línea vacía
ax.set_xlim(0, 10)
ax.set_ylim(20, 35)

x_data = []
y_data = []
while True:
    x_data.append(j)
    y_data.append(temp)

    # Actualiza los datos de la línea existente
    linea.set_data(x_data, y_data)
    if j < 10:
        ax.set_xlim(0, 10)         # Al principio, mantenemos ventana fija
    else:
        ax.set_xlim(j-10, j+1)     # Ventana deslizante de 10 valores
    
    ax.set_xticks(range(int(ax.get_xlim()[0]), int(ax.get_xlim()[1]) + 1, 1))
    print(y_data)
    plt.title(f"Temp actual:  {temp} °C")
    plt.draw()
    plt.pause(0.5)
    temp = random.randint(25, 30)  # Valor entero entre 25 , 30 (incluidos)
    j+= 1
plt.ioff()
plt.show()