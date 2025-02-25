from pyedflib import highlevel
import pyedflib as plib
import os

r1 = [3,7,11]   # Realized One Hand (Left or Right)
i1 = [4,8,12]   # Imagined One Hand (Left or Right)
r2 = [5,9,13]   # Realized Two (Hands or Feet)
i2 = [6,10,14]  # Imagined Two (Hands or Feet)

codes = {'IL':(i1,'T1',0),'IR':(i1,'T2',1),'ILR':(i2,'T1',2),'IF':(i2,'T2',3),\
		'RL':(r1,'T1',4),'RR':(r1,'T2',5),'RLR':(r2,'T1',6), 'RF':(r2,'T2',7)}

def loadEEG(subject, record, path_files=os.path.join(os.getcwd(), "files")):  #lectura del .edf
	# formatting
	if isinstance(record, int):
		record = "{:02d}".format(record)
	if isinstance(subject, int):
		subject = "{:03d}".format(subject)

	path = os.path.join(path_files, "S" + subject, "S" + subject + "R" + record +'.edf')

	signals, signal_headers, header = highlevel.read_edf(path)

	return signals, signal_headers, header


def GetSignal(subject, tarea, sample_rate=160, segment_length=1280, selected_channels=None):
	'''
	GetSignal():
	Entrada:
	- subject: número de sujeto
	- tarea: 'IL', 'IR', 'ILR', 'IF', 'RL', 'RR', 'RLR', 'RF' (ver codes)
	- sample_rate: tasa de muestreo (Hz)
	- segment_length: longitud deseada del segmento (número de muestras)
	- selected_channels: lista de nombres de canales a seleccionar, si es None, usa todos.
	- 640 corresponde a los 4 seg a 160 Hz

	Salida:
	- sujeto: número de sujeto
	- data: lista de arrays de señal, cada array tiene tamaño (n_canales, segment_length)
	- labels: lista de etiquetas correspondientes a cada segmento
	- channels: nombres de canales seleccionados
	'''

	data = []  # Almacena los recortes de señales
	labels = []  # Almacena los numeros correspondientes a cada task
	channels = []  # Nombres de los canales seleccionados

	# Obtener información de la tarea
	run, T, label = codes[tarea]

	per_run = []
	# Recorrer los índices en 'run' (r1, i1, r2, i2)
	for irec in run:
		# Cargar las señales usando el sujeto y registro
		signals, signal_headers, header = loadEEG(subject, irec)

		# Extraer los nombres de los canales
		channel_names = [header['label'] for header in signal_headers]

		# Si no se especifican canales seleccionados, usar todos los canales disponibles
		if selected_channels is None:
			selected_channels = channel_names  # Usa todos los canales disponibles

		# Filtrar solo los canales seleccionados
		try:
			selected_indices = [channel_names.index(ch) for ch in selected_channels]
		except ValueError as e:
			print(f"Error: Canal {e} no encontrado en los nombres de canales disponibles \
			{channel_names}")
			return subject, [], [], []

		# Filtrar las señales según los índices de canales seleccionados
		signals = signals[selected_indices, :]
		channels = [channel_names[i] for i in selected_indices]

		# Buscar anotaciones relevantes (buscando índices)
		indices = []
		index = 0
		for notas in header['annotations']:
			if notas[2] == T:
				indices.append(index)
			index += 1
			
		points = 400.0 # points guarda cuántos puntos antes del estímulo vamos a usar

		for i in indices:
			event_index = header['annotations'][i][0]
			ti = int(sample_rate * event_index - points) 
			tf = int(sample_rate * event_index + 640)  
			recorte = signals[:, ti:tf]

			# Verificar longitud del recorte
			if recorte.shape[1] == segment_length:
				data.append(recorte)  # Agregar recorte a la lista de datos
				labels.append(label)  # Agregar etiqueta correspondiente
			else:
				print(f'Se descarta {subject} - {tarea}: longitud de recorte incorrecta '
				f'({recorte.shape[1]} en lugar de {segment_length})')
		per_run.append(len(indices))
	# Verificar si no se encontraron segmentos válidos
	if len(data) == 0:
		print(f'Se descarta {subject} - {tarea}: no se encontraron segmentos válidos.')
		return subject, [], [], []

	

	return subject, data, per_run, labels, channels

