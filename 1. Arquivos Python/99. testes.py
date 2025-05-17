import math

#### teste para ver angulo real
#Coordenadas das ancoras
anchor_coords = {
    1: {'x': -0.84, 'y': 0.54},  # A01
    2: {'x': -7.14, 'y': 7.74},  # A02
    3: {'x': -1.14, 'y': 7.74},  # A03
    4: {'x': -7.74, 'y': 0.84},  # A04
}

test_coords = {
    'C1P1': {'x': -1.14, 'y': 0.39}, 
    'C2P3': {'x': -3.54, 'y': 4.44}, 
    'C3P1': {'x': -1.14, 'y': 6.84}, 
    'C3P5': {'x': -5.94, 'y': 6.84}, 
    
}

for anchor_id, acoords in anchor_coords.items():
    for test_id, tcoords in test_coords.items(): 
        xa = acoords['x']
        ya = acoords['y']
        xt = tcoords['x']
        yt = tcoords['y']

        dy = yt - ya
        dx = xt - xa

        ladoh = 'direita' if xa > xt else 'esquerda'
        ladov = 'cima' if ya > yt else 'baixo'
        
        # Calcular o ângulo entre a âncora e o ponto de teste
        if ladoh == 'direita':
            if ladov == 'cima':
                angulo = 180 + math.degrees(math.atan2(dy, dx))
            else:
                angulo = 180 - math.degrees(math.atan2(dy, dx))
        elif ladoh == 'esquerda':
            if ladov == 'cima':
                angulo = -math.degrees(math.atan2(dy, dx)) 
            else:
                angulo = math.degrees(math.atan2(dy, dx))

        print(f'Anchor: {anchor_id}, Teste Point: {test_id}, Angulo: {angulo}')