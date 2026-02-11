import matplotlib.pyplot as plt

# Данные строго по твоему запросу
labels = ['Main (65%)', 'Growth (20%)', 'Other (15%)']
sizes = [65, 20, 15]
colors = ['#00E5FF', '#0082FF', '#004BB5'] # Неоновые синие оттенки

fig, ax = plt.subplots(figsize=(6, 6))
fig.patch.set_facecolor('black') # Черный фон как в RILLET

# Рисуем "бублик"
wedges, texts, autotexts = ax.pie(
    sizes, labels=labels, autopct='%1.0f%%', 
    startangle=90, colors=colors, 
    pctdistance=0.85, textprops={'color':"w"}
)

# Делаем дырку в центре
centre_circle = plt.Circle((0,0), 0.70, fc='black')
fig.gca().add_artist(centre_circle)

plt.title("RILLET Market Analysis", color='white', pad=20)
ax.axis('equal')  
plt.show()
