# Rules to define what is an appointment for aesthetic services = Pró-Corpo

# Appointment info
procedures_es = ['AVALIAÇÃO ESTÉTICA', 'AVALIAÇÃO INJETÁVEIS E INVASIVOS']
desired_status_es = ['Confirmado', 'Agendado']

# Stores:
stores_exclude_es = ['PRAIA GRANDE', 'HOMA', 'PLÁSTICA']
stores_include_es = [] # all, except stores_exclude

# Useful intervals:
intervals_es = {
    '-1': 'd1',
    '-2': 'd2',
    '-3': 'd3',
    '-4': 'd4',
    '-5': 'd5',
    '1': 'dMaisum'
}

interval_time = input - today()