from __future__ import absolute_import, division, print_function, unicode_literals
import numpy as np
import pdb
import pandas as pd
import os.path
from tensorflow import keras
import tensorflow as tf
import numpy as np
from time import process_time
from scipy import stats


import matplotlib as mpl
import matplotlib.pyplot as plt
mpl.rcParams['figure.figsize'] = (8, 6)
mpl.rcParams.update({'font.size': 15})
mpl.rcParams['axes.grid'] = False

class NeuralNetworkModel():
  EPOCHS = 10
  BATCH_SIZE = 256
  STEP = 1

  def __init__(self, x_file, y_file, target_variable_name, steps_in_future = 30, directory = None, 
    past_history = 60*4, evaluation_interval = 200):
    self.x_file = x_file
    self.y_file = y_file
    self.steps_in_future = steps_in_future
    self.target_variable_name = target_variable_name
    self.directory = directory
    self.past_history = past_history
    self.evaluation_interval = evaluation_interval
    self.selected_model = 'model_{}_seconds_forecast_new_loadgen.h5'.format(steps_in_future)
    self.selected_model = os.path.join(self.directory, self.selected_model)
    self.single_step_model = None
    self.input_shape = (past_history, 15)
    tf.random.set_seed(13)

  def multivariate_data(self, dataset, target, start_index, end_index, history_size,
                        target_size, step, single_step=False):
    data = []
    labels = []
    start_index = start_index + history_size
    if end_index is None:
      end_index = len(dataset) - target_size

    for i in range(start_index, end_index):
      indices = range(i-history_size, i, step)
      data.append(dataset[indices]) 

      if single_step:
        labels.append(target[i+target_size])
      else:
        labels.append(target[i:i+target_size])

    return np.array(data), np.array(labels)

  def merge_dataset(self):
    x_raw = pd.read_csv(self.x_file)
    y_raw = pd.read_csv(self.y_file)
    #y_raw = self.drop_numerical_outliers(y_raw)
    merged_dataset = pd.merge(x_raw, y_raw, how='inner', on=['timestamp'])
    self.x_features = x_raw.columns.values.tolist()
    self.x_features.remove('timestamp')
    self.considered_features = self.x_features + [self.target_variable_name]
    features = merged_dataset[self.considered_features]
    features.index = merged_dataset['timestamp']
    self.target_variable_index = features.columns.to_list().index(self.target_variable_name)
    self.dataset = features.values

  def normalize_dataset(self):
    self.data_mean = self.dataset.mean(axis=0)
    self.data_std = self.dataset.std(axis=0)
    self.dataset = (self.dataset-self.data_mean)/self.data_std

  def denormalize_value(self, value):
    return value * self.data_std[self.target_variable_index] + self.data_mean[self.target_variable_index]

  def preproccess_dataset(self):
    self.merge_dataset()
    self.normalize_dataset()

    dataset_x = np.delete(self.dataset, [self.target_variable_index], axis=1)
    dataset_y = self.dataset[:,self.target_variable_index]

    self.train_split = int(dataset_y.shape[0]*0.7)#3h de experimento total #12*60*8 #6480 #int(7200*0.75) #300000
    self.buffer_size = int(dataset_y.shape[0]/5)#1000
    self.x_train_single, self.y_train_single = self.multivariate_data(dataset_x, dataset_y, 0, #(dataset, dataset[:, 5], 0,
                                                      None, self.past_history,
                                                      self.steps_in_future, self.STEP,
                                                      single_step=True)
    self.x_val_single, self.y_val_single = self.multivariate_data(dataset_x, dataset_y, #dataset[:, 5],
                                                  self.train_split, None, self.past_history,
                                                  self.steps_in_future, self.STEP,
                                                  single_step=True)

    self.input_shape = self.x_train_single.shape[-2:]

  def create_time_steps2(self, delta, size):
    return list(range(self.train_split+delta, self.train_split+size+delta))

  def create_time_steps(self, begin, end=0):
    time_steps = []
    for i in range(-begin, end, 1):
      time_steps.append(i)
    return time_steps

  def show_plot(self, plot_data, delta, title):
    labels = ['Real', 'Forecast', 'Average']
    marker = ['.', '.', '-']
    colors = ['#56a64b', '#8ab8ff', '#6f4044']
    plt.title(title)
    for i, x in enumerate(plot_data[:-1]):
      if i:
        time_steps = self.create_time_steps2(delta, plot_data[0].shape[0])
        plt.plot(time_steps, plot_data[i], marker[i], markersize=10,
                label=labels[i])
      else:
        time_steps = self.create_time_steps2(0, plot_data[0].shape[0])
        plt.plot(time_steps, plot_data[i], marker[i], label=labels[i], color = colors[i])

    plt.plot(time_steps, [plot_data[-1]]*len(time_steps), marker[-1], label=labels[-1])

    plt.legend(ncol= 1, loc="upper left")
    plt.ylim(0,300)
    plt.xlabel('Time (s)')
    plt.ylabel('KPI value (ms)')

  def plot_train_history(self, history, title):
    loss = history.history['loss']
    val_loss = history.history['val_loss']

    epochs = range(len(loss))

    plt.figure()

    plt.plot(epochs, loss, 'b', label='Training loss')
    plt.plot(epochs, val_loss, 'r', label='Validation loss')
    plt.title(title)
    plt.legend()

    #plt.show()

  def drop_numerical_outliers(self, df, z_thresh=3):
    # Constrains will contain `True` or `False` depending on if it is a value below the threshold.
    constrains = df.select_dtypes(include=[np.number]) \
        .apply(lambda x: np.abs(stats.zscore(x)) < z_thresh, reduce=False) \
        .all(axis=1)
    # Drop (inplace) values set to be rejected
    df.drop(df.index[~constrains], inplace=True)
    return df

  def create_model(self, overwrite = True):
    file_name = 'model_{}_seconds_forecast_{}_past_history.h5'.format(self.steps_in_future, self.past_history)
    model_path = os.path.join(self.directory,file_name)
    self.preproccess_dataset()

    if os.path.exists(model_path) and not overwrite:
      self.single_step_model = keras.models.load_model(model_path)
      val_data_single = tf.data.Dataset.from_tensor_slices((self.x_val_single, self.y_val_single))
      val_data_single = val_data_single.batch(self.BATCH_SIZE).repeat()

    else:
      train_data_single = tf.data.Dataset.from_tensor_slices((self.x_train_single, self.y_train_single))
      train_data_single = train_data_single.cache().shuffle(self.buffer_size).batch(self.BATCH_SIZE).repeat()
      val_data_single = tf.data.Dataset.from_tensor_slices((self.x_val_single, self.y_val_single))
      val_data_single = val_data_single.batch(self.BATCH_SIZE).repeat()

      self.single_step_model = tf.keras.models.Sequential()

      self.single_step_model.add(tf.keras.layers.LSTM(32,
                                                input_shape=self.x_train_single.shape[-2:]))
      self.single_step_model.add(tf.keras.layers.Dense(1))

      #multi_step_model.compile(optimizer=tf.keras.optimizers.RMSprop(clipvalue=1.0), loss='mae')
      self.single_step_model.compile(optimizer=tf.keras.optimizers.RMSprop(), loss='mae', metrics=['mape'])

      self.single_step_history = self.single_step_model.fit(train_data_single, epochs=self.EPOCHS,
                                                  steps_per_epoch=self.evaluation_interval,
                                                  validation_data=val_data_single,
                                                  validation_steps=50)

      self.plot_train_history(self.single_step_history,
                   '{} second(s) forecast, {} history size \nTraining and Validation Histories'.format(self.steps_in_future, self.past_history))
      figure_path = os.path.join(self.directory, '{}_s_forecast_{}_past_history_train_history.png'.format(self.steps_in_future, self.past_history))
      plt.savefig(figure_path)
      self.single_step_model.save(model_path)

    y_predictions = self.single_step_model.predict(self.x_val_single).flatten()
    y_predictions =  self.denormalize_value(y_predictions)
    self.y_val_single = self.denormalize_value(self.y_val_single)
    y_predictions_naive = self.y_val_single.mean()

    mape_rna = self.mape(y_predictions, self.y_val_single)
    mape_naive = self.mape(y_predictions_naive, self.y_val_single)

    print("Steps: {} in future, history size: {}, MAPE: RNA {}, MAPE: naive {}".
      format(self.steps_in_future, self.past_history, mape_rna, mape_naive))
    plt.clf()
    title = '{}s in future, {}s window'.format(self.steps_in_future, self.past_history)
    self.show_plot([self.y_val_single, y_predictions, y_predictions_naive], self.steps_in_future, title)

    figure_path = os.path.join(self.directory, '{}_seconds_forecast_{}_past_history.png'.
      format(self.steps_in_future, self.past_history))
    #plt.show()
    plt.savefig(figure_path)

  def normalize_input(self, input_metrics):
    self.input_metrics_mean = input_metrics.mean(axis=1)
    self.input_metrics_std = input_metrics.std(axis=1)
    input_metrics = input_metrics-self.input_metrics_mean
    input_metrics = input_metrics/self.input_metrics_std
    return np.nan_to_num(input_metrics)

  def load_model(self):
    self.merge_dataset()
    self.normalize_dataset()
    self.single_step_model = keras.models.load_model(self.selected_model)

  def forecast(self, input_metrics):
    if self.single_step_model == None:
      self.single_step_model = keras.models.load_model(self.selected_model)

    input_metrics = self.normalize_input(input_metrics)
    y_prediction = self.single_step_model.predict(input_metrics).flatten()

    return self.denormalize_value(y_prediction)[0]

  def nmae(self, predicted, real):
    return (np.absolute(predicted - real).mean())/real.mean()

  def mape(self, predicted, real):
    return np.sum(np.absolute((real - predicted)/real))*100/len(real)

if __name__ == "__main__":
  directories = ['slices_files/slice_1/flavor_1', 'slices_files/slice_1/flavor_2']
  steps_in_future = [1, 30, 60, 120]
  past_histories= [60*4, 60*8]
  # directories = ['slices_files/slice_1/flavor_1']
  # steps_in_future = [1]
  # past_histories= [60*4]
  sla_metric_name = 'R_99'
  evaluation_interval = 100
  overwrite = True
  for directory in directories:
    print("** Creating models in directory {} **".format(directory))
    x_file = os.path.join(directory, 'x_selected_metrics.csv')
    y_file = os.path.join(directory, 'y_metrics.csv')
    for value in steps_in_future:
      for past_history in past_histories:
        model = NeuralNetworkModel(x_file,y_file,sla_metric_name,value,directory=directory,
          past_history=past_history, evaluation_interval = evaluation_interval)
        print("** Creating model for {} steps in future and {} past history size ** ".format(value,past_history))
        ini_fit = process_time()
        model.create_model(overwrite = overwrite)
        end_fit = process_time()

        print("** Time elapsed: {} **".format(end_fit-ini_fit))
