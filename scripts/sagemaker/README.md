# SageMaker endpoint for StreamVault ED-LSTM

The API invokes **`SAGEMAKER_ENDPOINT_NAME`** with JSON:

```json
{"instances": [[[cpu, req, lat, net, err], ...]]}
```

The first `instances` entry is a **24×5** window (same order as `LocalTensorFlowInferenceAdapter.FEATURE_ORDER`).

Nominal simulated traffic (dashboards + fallback windows in `shared/metrics_nominal_demo.py`) uses **CPU as percentage 0–100** (~31–49% at steady state), **`error_rate` as a fraction** (typically ~1–2%), and `request_rate` / `latency_ms` / `network_mbps` in production-like bands. Align payload scale with whatever the deployed model was trained on.

The endpoint should respond with JSON containing **`predictions`**:

- **Preferred:** list of forecast rows, shape `(horizon, 5)` — one row per future timestep (matches training `horizon=6`).
- **Also accepted:** flat list of length 5 (single next step).

Optional **`predicted_future`:** same as `predictions` for chart compatibility.

## Package the model

1. Train locally (synthetic data is fine):

   ```bash
   PYTHONPATH=. python services/ml_predictor/train.py
   ```

2. Build **`model.tar.gz`** for a TensorFlow serving-style bundle:

   ```bash
   rm -rf /tmp/sv-sm && mkdir -p /tmp/sv-sm/1 /tmp/sv-sm/code
   cp services/ml_predictor/models/ed_lstm_demo.keras /tmp/sv-sm/1/
   cp scripts/sagemaker/inference.py /tmp/sv-sm/code/
   tar -czvf model.tar.gz -C /tmp/sv-sm .
   ```

3. Upload to S3 and create a model + endpoint with the **SageMaker Python SDK** or **Console** using a **TensorFlow inference image** for your region (see [TensorFlow on SageMaker](https://docs.aws.amazon.com/sagemaker/latest/dg/tfdeploy-model.html)).

4. Set on the API host (see `.env.aws.example`):

   - `APP_MODE=aws`
   - `USE_REAL_AWS=true`
   - `AWS_REGION` = endpoint region
   - `SAGEMAKER_ENDPOINT_NAME` = your endpoint name
   - `ML_USE_SAGEMAKER=true` so the API uses SageMaker even if a local `.keras` file exists

5. IAM: allow `sagemaker:InvokeEndpoint` on that endpoint for the role or user running `uvicorn` (see `scripts/aws/iam-streamvault-app-policy.json`).

## Smoke test

```bash
aws sagemaker-runtime invoke-endpoint \
  --endpoint-name YOUR_ENDPOINT \
  --content-type application/json \
  --body '{"instances": [[[40,205,43,53,0.012],[39,212,41,62,0.014]]]}' \
  --cli-binary-format raw-in-base64-out \
  /tmp/out.json && cat /tmp/out.json
```

(Use a full 24-row window in real tests; the snippet illustrates payload shape.)
