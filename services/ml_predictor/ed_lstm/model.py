from __future__ import annotations

"""
Encoder-Decoder LSTM for multivariate cloud metrics (seq2seq-style).

Input: past window (lookback x n_features)
Output: future window (horizon x n_features)

Kept compact for coursework: 2-layer encoder, 2-layer decoder with RepeatVector + TimeDistributed Dense.
"""


import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers


def build_ed_lstm(
    lookback: int,
    horizon: int,
    n_features: int,
    lstm_units: int = 32,
) -> keras.Model:
    encoder_inputs = keras.Input(shape=(lookback, n_features), name="encoder_inputs")

    enc = layers.LSTM(lstm_units, return_sequences=True, name="enc_lstm_1")(encoder_inputs)
    enc = layers.LSTM(lstm_units, return_state=False, name="enc_lstm_2")(enc)

    repeat = layers.RepeatVector(horizon, name="repeat_future")(enc)
    dec = layers.LSTM(lstm_units, return_sequences=True, name="dec_lstm_1")(repeat)
    dec = layers.LSTM(lstm_units, return_sequences=True, name="dec_lstm_2")(dec)
    outputs = layers.TimeDistributed(layers.Dense(n_features), name="future_vectors")(dec)

    model = keras.Model(encoder_inputs, outputs, name="ed_lstm_cloud_metrics")
    model.compile(optimizer=keras.optimizers.Adam(1e-3), loss=keras.losses.Huber())

    return model


def anomaly_score(y_true: tf.Tensor, y_pred: tf.Tensor) -> tf.Tensor:
    return tf.reduce_mean(tf.abs(y_true - y_pred), axis=[1, 2])
