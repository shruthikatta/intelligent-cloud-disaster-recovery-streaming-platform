# SageMaker inference endpoint (StreamVault ED-LSTM)

This is a short companion to **`scripts/sagemaker/README.md`**.

## When to use it

- You want **`SageMaker Runtime`** (`invoke_endpoint`) instead of loading **`ed_lstm_demo.keras`** on the API host.

## App configuration

Set in `.env` / `.env.aws`:

| Variable | Value |
|----------|--------|
| `APP_MODE` | `aws` |
| `USE_REAL_AWS` | `true` |
| `AWS_REGION` | Same region as the endpoint |
| `SAGEMAKER_ENDPOINT_NAME` | Name shown in SageMaker console |
| **`ML_USE_SAGEMAKER`** | **`true`** — forces SageMaker even if `ML_MODEL_PATH` file exists on disk |

IAM for the process running FastAPI must allow **`sagemaker:InvokeEndpoint`** on that endpoint.

## Endpoint contract

- **Request body:** `{"instances": [window]}` where `window` is a `24 × 5` array (CPU, request rate, latency, network Mbps, errors).
- **Response JSON:** must include **`predictions`** — either a list of horizon rows `[[...], ...]` (preferred) or a single flat row of length 5.

The handler in **`scripts/sagemaker/inference.py`** returns `{"predictions": rows}` with `rows = model_output[0].tolist()` (ED-LSTM outputs shape `(1, horizon, 5)`).

## Related code

- **`cloud_adapters/aws/sagemaker/model_inference_adapter.py`** — invokes the endpoint and parses `predictions`.
- **`cloud_adapters/dependency_factory.py`** — selects SageMaker when `ML_USE_SAGEMAKER` is set (and AWS + endpoint name), or when there is no local `.keras` file but AWS + endpoint are configured.
