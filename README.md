# Real-time ECG Heart Rate Monitor

For NTHU DSP_Lab12. \
Implementation of a Real-time ECG signal processing using python.

![ECG Moniter](https://github.com/user-attachments/assets/90882ef3-c0e2-471e-a846-f2da0b267410)

## Requirements
- Python 3.10+

## Installation
Clone this repository and install the dependencies.

### Using [`uv`](https://github.com/astral-sh/uv) (Recommended)
```bash
uv sync
```

### Using `pip`
```bash
# Create a virtual environment (optional but recommended)
python3 -m venv .venv
pip intstall -r requirement.txt
```
## Usage
### Using `uv` (Recommended)
```bash
uv run main.py
```
### Using `pip`
```bash
source .venv/bin/activate # Windows / Linux Bash
python main.py
```

## Configuration
You can customize the signal processing params in `config.py`:

- `port`: Serial port (e.g., `/dev/ttyACM0`, `COM3`)
- `baud_rate`: Serial Communication baud rate (Default: `115200`)
- `batch_size`: Number of samples to process at once (Default: `10`).

- Other filter params for detailed, lookup `config.py`

## License

This project is licensed under the **MIT License** ([LICENSE](LICENSE) or https://opensource.org/licenses/MIT).

Unless you explicitly state otherwise, any contribution intentionally submitted for inclusion in this project by you shall be licensed as above, without any additional terms or conditions.