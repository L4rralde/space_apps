# Import libraries
import numpy as np
import pandas as pd
from obspy import read
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import os
from scipy import signal
from matplotlib import cm


cat_directory = f"{os.environ["SPACE"]}/data/lunar/training/catalogs/"
cat_file = cat_directory + 'apollo12_catalog_GradeA_final.csv'
data_directory = f"{os.environ["SPACE"]}/data/lunar/training/data/S12_GradeA/"
cat = pd.read_csv(cat_file)

## COmbinado
def process_data_max(data, window_max, window_filter):
    max_data = np.zeros(len(data))
    for i in range(len(data) - window_max):
        max_data[i] = np.max(data[i:i+window_max])
    # Aplicamos un filtro de ventana a los maximos
    max_data_filtered = np.zeros(len(data))
    for i in range(len(data) - window_filter):
        max_data_filtered[i] = np.mean(max_data[i:i+window_filter])

    return max_data_filtered
    
def good_intervals(processed_data, threshold, K):

    # Obtenemos los intervalos buenos
    i = 0
    relevant_times = []
    while i < len(processed_data):
        if processed_data[i] > threshold:
            j = i
            time_to_return = 0
            while processed_data[i] > threshold:
                i += 1
                time_to_return += 1
                if i >= len(processed_data):
                    i -= 1
                    break
            if time_to_return > K:
                relevant_times.append([j, j+time_to_return])
            continue
        i += 1

    return relevant_times

def get_end(interval, window, processed_data, tol):
    # Pasamos una ventana en los datos y obtenemos el promedio
    end = interval[1]
    data_media = [np.mean(processed_data[end:end+window])]
    end += 1
    cont = 0
    while (end < len(processed_data) - 1):
        data_media.append(np.mean(processed_data[end:end+window]))
        end += 1
        cont += 1
        if(abs(data_media[i] - data_media[i-1]) < tol):
            return end
    return end

def refine_intervals_forward(processed_data, relevant_times, tol):
    # Calculamos la mediana fuera de los intervalos buenos
    outside_points = processed_data.tolist()
    last_index = len(processed_data) - 1
    for interval in relevant_times:
        # Eliminamos los puntos de interval
        for i in range(interval[0], interval[1]):
            outside_points[i] = outside_points[last_index]
            last_index -= 1
    outside_points = np.array(outside_points[:last_index])
    median_outside = np.median(outside_points)

    # Refinamos los intervalos buenos
    refined_times = []
    for interval in relevant_times:
        a,b = refined_times[-1] if len(refined_times) > 0 else (0,0)
        if(a <= interval[1] <= b):
            continue
        # Refinamos el final
        new_end = interval[1]
        while new_end < (len(processed_data)-1) and abs(processed_data[new_end] - median_outside) > tol:
            new_end += 1
        refined_times.append((interval[0], new_end))

    return refined_times

def rel_time_to_abs_time(rel_time, starttime):
    tr_times_dt = []
    for tr_val in rel_time:
        tr_times_dt.append(starttime + timedelta(seconds=tr_val))
    return tr_times_dt


class Prediction:
    def __init__(self) -> None:
        self.test_filename = None
        self.arrival = None
        self.t = None
        self.power = None
        self.relevant_times = None
        self.max_index = None
        self.threshold = None

class Model:
    def __init__(self) -> None:
        self.prediction = Prediction()

    def predict(self, i) -> None:
        row = cat.iloc[i]
        relevant_points = 0
        total_points = 0
        arrival_time = datetime.strptime(row['time_abs(%Y-%m-%dT%H:%M:%S.%f)'],'%Y-%m-%dT%H:%M:%S.%f')
        test_filename = row.filename
        mseed_file = f'{data_directory}{test_filename}.mseed'
    
        st = read(mseed_file)
        # This is how you get the data and the time, which is in seconds
        tr = st.traces[0].copy()
        tr_times = tr.times()
        tr_data = tr.data

        # Start time of trace (another way to get the relative arrival time using datetime)
        starttime = tr.stats.starttime.datetime
        arrival = (arrival_time - starttime).total_seconds()
        # Create a vector for the absolute time
        tr_times_dt = rel_time_to_abs_time(tr_times, starttime)
        
        # Going to create a separate trace for the filter data
        st_filt = st.copy()
        #st_filt.filter('bandpass',freqmin=minfreq,freqmax=maxfreq)
        tr_filt = st_filt.traces[0].copy()
        tr_times_filt = tr_filt.times()
        tr_data_filt = tr_filt.data

        f, t, sxx = signal.spectrogram(tr_data_filt, tr_filt.stats.sampling_rate, mode='magnitude')
        # Sum over all sxx values to get the power
        power = np.mean(sxx, axis=0)

        threshold = np.percentile(power, 95)

        relevant_times = good_intervals(power, threshold, 20)
        relevant_times = refine_intervals_forward(power, relevant_times, 5e-12)
        #relevant_times_backward = refine_intervals_backward(power, relevant_times_forward, 1e-12)

        total_points += len(power)
        for interval in relevant_times:
            relevant_points += interval[1] - interval[0] + 1

        # # Asignamos los indices de forward a relevant_times[i][1] 
        # cont = 0
        # for foward in relevant_times_forward:
        #     relevant_times[cont][1] = foward[1]
        #     cont += 1
            
        # Sumaremos en intervalos de 10 segundos
        sum_interval = 50
        
        max_index = []
        for i_min, i_max in relevant_times:
            sum_power = []
            for i in range(i_min-50, i_max, 1):
                sum_power.append([np.sum(power[i:i+sum_interval]),i])
            # Donde hallemos el maximo, extraemos el indice de la tupla (suma, indice)
            max_index.append(max(sum_power)[1])
    
        self.prediction.t = t
        self.prediction.power = power
        self.prediction.test_filename = test_filename
        self.prediction.arrival = arrival
        self.prediction.max_index = max_index
        self.prediction.threshold = threshold
        self.prediction.relevant_times = relevant_times
        return self.prediction


    def plot(self) -> None:
        fig,ax = plt.subplots(1,1,figsize=(10,3))

        t = self.prediction.t
        power = self.prediction.power
        test_filename = self.prediction.test_filename
        arrival = self.prediction.arrival
        max_index = self.prediction.max_index
        threshold = self.prediction.threshold
        relevant_times = self.prediction.relevant_times

        # Plot the power
        ax.plot(t, power)

        ax.set_ylabel('Power')
        ax.set_xlabel('Time [sec]')
        ax.set_title(f'{test_filename} Power', fontweight='bold')
        # Add the arrival time
        ax.axvline(x = arrival, color='red',label='Rel. Arrival')
        
        #ax.set_ylim([0, 1e-19])
        for index in max_index:
            ax.axvline(x = t[index], color='blue',label='Max Power', linestyle='--')
        
        ax.axhline(y=threshold, c='green', label='95th Percentile')
        
        # Plot the relevant times
        for time in relevant_times:
            #ax.axvline(x=t[time[0]], c='purple', label='Relevant Time')
            ax.axvline(x=t[time[1]], c='purple', label='Relevant Time')
        ax.legend(loc='upper left')
        # Guardamos la figura
        fig.savefig(f'{test_filename}_power.png')
        plt.close(fig)


if __name__ == "__main__":
    predictor = Model()
    predictor.predict(1)
    predictor.plot()
