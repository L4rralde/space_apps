import os
from datetime import datetime, timedelta
from copy import copy

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import cm
from obspy import read
from scipy import signal


cat_directory = f"{os.environ['SPACE']}/data/lunar/training/catalogs/"
cat_file = cat_directory + 'apollo12_catalog_GradeA_final.csv'
data_directory = f"{os.environ['SPACE']}/data/lunar/training/data/S12_GradeA/"
cat = pd.read_csv(cat_file)

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


def get_backward_index(relevant_times, window, processed_data):
    variance_index = []
    for time in relevant_times:
        variance = []
        for i in range(time[0]-5,time[0], 1):
            variance.append([np.var(processed_data[i:i+window]),i])
        variance_index.append(max(variance)[1])
    
    return variance_index

def rel_time_to_abs_time(rel_time, starttime):
    tr_times_dt = []
    for tr_val in rel_time:
        tr_times_dt.append(starttime + timedelta(seconds=tr_val))
    return tr_times_dt


class Prediction:
    def __init__(self) -> None:
        self.mseed_file = None
        self.test_filename = None
        self.arrival = None
        self.t = None
        self.f = None
        self.sxx = None
        self.power = None
        self.relevant_times = None
        self.variance_index = None
        self.threshold = None
        self.tr_data_filt = None
        self.tr_times_filt = None
        self.tr_filt = None
        self.state: str = "EMPTY"

    def __eq__(self, other: object) -> bool:
        attrs = [
            "t", "f", "sxx", "power", "relevant_times", "variance_index",
            "threshold", "tr_data_filt", "tr_times_filt", "tr_filt"
        ]
        for attr in attrs:
            mine = self.__getattribute__(attr)
            yours = other.__getattribute__(attr)
            mismatch = np.array(mine != yours)
            if mismatch.any():
                print(f"{attr} mismatch")
        return True

class Model:
    def __init__(self) -> None:
        self.prediction = Prediction()

    def clear(self) -> None:
        self.prediction = Prediction()
        self._mseed_file: str = ""

    def open(self, mseed_file) -> "Prediction":
        if not os.path.exists(mseed_file):
            raise Exception("NOT SUCH FILE")
        st_filt = read(mseed_file)

        #st_filt.filter('bandpass',freqmin=minfreq,freqmax=maxfreq)
        tr_filt = st_filt.traces[0].copy()
        tr_times_filt = tr_filt.times()
        tr_data_filt = tr_filt.data
        self.prediction.state = "OPEN"
        self.prediction.tr_filt = tr_filt
        self.prediction.tr_times_filt = tr_times_filt
        self.prediction.tr_data_filt = tr_data_filt
        return copy(self.prediction)

    def transform(self, percentile: float = 0.95) -> "Prediction":
        tr_times_filt = self.prediction.tr_times_filt
        tr_data_filt = self.prediction.tr_data_filt
        tr_filt = self.prediction.tr_filt
        f, t, sxx = signal.spectrogram(tr_data_filt, tr_filt.stats.sampling_rate, mode='magnitude')
        # Sum over all sxx values to get the power
        power = np.mean(sxx, axis=0)
        threshold = np.percentile(power, percentile)
        self.prediction.state = "TRANSFORM"
        self.prediction.f = f
        self.prediction.t = t
        self.prediction.sxx = sxx
        self.prediction.power = power
        self.prediction.threshold = threshold
        return copy(self.prediction)

    def get_intervals(self) -> "Prediction":
        self.prediction.state = "INTERVALS"
        self.prediction.relevant_times = good_intervals(
            self.prediction.power, 
            self.prediction.threshold,
            20
        )
        return copy(self.prediction)

    def refine_intervals(self) -> "Prediction":
        self.prediction.relevant_times = refine_intervals_forward(
            self.prediction.power,
            self.prediction.relevant_times,
            5e-12
        )
        return copy(self.prediction)

    def refine_intervals_backward(self) ->  "Prediction":
        variance_index = get_backward_index(
            self.prediction.relevant_times,
            3,
            self.prediction.power
        )
        total_points = len(self.prediction.power)
        relevant_points = 0
        for interval in self.prediction.relevant_times:
            relevant_points += interval[1] - interval[0] + 1
        self.prediction.state = "BACKWARD"
        self.prediction.variance_index = variance_index
        return copy(self.prediction)

    def predict_pipeline(self, mseed_file, *, arrival_time=None, percentile=95) -> None:
        self.open(mseed_file)
        self.transform(percentile)
        self.get_intervals()
        self.refine_intervals()
        self.refine_intervals_backward()
        return copy(self.prediction)

    def predict(self, mseed_file, *, arrival_time=None, percentile=95) -> None:
        if not os.path.exists(mseed_file):
            raise Exception("NOT SUCH FILE")

        st = read(mseed_file)
        # This is how you get the data and the time, which is in seconds
        tr = st.traces[0].copy()
        tr_times = tr.times()
        tr_data = tr.data

        relevant_points = 0
        total_points = 0

        # Start time of trace (another way to get the relative arrival time using datetime)
        starttime = tr.stats.starttime.datetime
        if arrival_time is not None:
            arrival = arrival = (arrival_time - starttime).total_seconds()
        else:
            arrival =  None
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


        threshold = np.percentile(power, percentile)

        relevant_times = good_intervals(power, threshold, 20)
        relevant_times = refine_intervals_forward(power, relevant_times, 5e-12)
        #relevant_times_backward = refine_intervals_backward(power, relevant_times_forward, 1e-12)
        variance_index = get_backward_index(relevant_times, 3, power)

        total_points += len(power)
        for interval in relevant_times:
            relevant_points += interval[1] - interval[0] + 1

    
        self.prediction.t = t
        self.prediction.f = f
        self.prediction.sxx = sxx
        self.prediction.power = power
        self.prediction.test_filename = os.path.basename(mseed_file)
        self.prediction.arrival = arrival
        self.prediction.threshold = threshold
        self.prediction.relevant_times = relevant_times
        self.prediction.variance_index = variance_index
        self.prediction.tr_filt = tr_filt
        self.prediction.tr_data_filt = tr_data_filt
        self.prediction.tr_times_filt = tr_times_filt
        return self.prediction


    def plot(self) -> None:
        t = self.prediction.t
        f = self.prediction.f
        power = self.prediction.power
        test_filename = self.prediction.test_filename
        arrival = self.prediction.arrival
        variance_index = self.prediction.variance_index
        threshold = self.prediction.threshold
        relevant_times = self.prediction.relevant_times
        sxx = self.prediction.sxx
        tr_data_filt = self.prediction.tr_data_filt
        tr_times_filt = self.prediction.tr_times_filt

        fig = plt.figure(figsize=(10, 10))
        ax = plt.subplot(2, 1, 1)
        ax.plot(tr_times_filt, tr_data_filt)
        if self.prediction.arrival is not None:
            ax.axvline(x = arrival, color='red',label='Rel. Arrival')
        
        #ax.set_ylim([0, 1e-19])
        # for index in max_index:
        #     ax.axvline(x = t[index], color='blue',label='Max Power', linestyle='--')
        for index in variance_index:
            ax.axvline(x = t[index], color='orange',label='Max Variance', linestyle='--')

        ax.axhline(y=threshold, c='green', label='95th Percentile')
        
        # Plot the relevant times
        for time in relevant_times:
            #ax.axvline(x=t[time[0]], c='purple', label='Relevant Time')
            ax.axvline(x=t[time[1]], c='purple', label='Relevant Time')
        ax.legend(loc='upper left')
        

        # Plot the power
        #ax.plot(t, power)
        ax2 = plt.subplot(2, 1, 2)
        vals = ax2.pcolormesh(t, f, sxx, cmap=cm.jet)
        cbar = plt.colorbar(vals, orientation="horizontal")

        ax2.set_ylabel('Power')
        ax2.set_xlabel('Time [sec]')
        ax2.set_title(f'{test_filename} Power', fontweight='bold')
        # Add the arrival time
        if self.prediction.arrival is not None:
            ax2.axvline(x = arrival, color='red',label='Rel. Arrival')
        
        #ax.set_ylim([0, 1e-19])
        # for index in max_index:
        #     ax.axvline(x = t[index], color='blue',label='Max Power', linestyle='--')
        for index in variance_index:
            ax2.axvline(x = t[index], color='orange',label='Max Variance', linestyle='--')

        ax2.axhline(y=threshold, c='green', label='95th Percentile')
        
        # Plot the relevant times
        for time in relevant_times:
            #ax2.axvline(x=t[time[0]], c='purple', label='Relevant Time')
            ax2.axvline(x=t[time[1]], c='purple', label='Relevant Time')
        ax2.legend(loc='upper left')
        # Guardamos la figura
        fig.savefig(f'{test_filename}_power.png')
        plt.close(fig)


if __name__ == "__main__":
    predictor = Model()
    predictor_pipe = Model()
    if "lunar" in cat_directory:
        percentile = 95
    else:
        percentile = 65
    for i in range(75):
        print(f"{i}/75")
        row = cat.iloc[i]
        arrival_time = datetime.strptime(row['time_abs(%Y-%m-%dT%H:%M:%S.%f)'],'%Y-%m-%dT%H:%M:%S.%f')
        test_filename = row.filename

        mseed_file = f'{data_directory}{test_filename}.mseed'
        predictor.predict(
            mseed_file, 
            arrival_time=arrival_time,
            percentile=percentile
        )
        predictor_pipe.predict_pipeline(
            mseed_file,
            arrival_time=arrival_time,
            percentile=percentile
        )
        if(predictor.prediction != predictor_pipe.prediction):
            break
        predictor_pipe.plot()
