# py_matrix_host

Host Python do acelerador.

Uso principal:

```powershell
    python main.py generate --n 128 --num-tests 1 --data-width 16 --acc-width 32 --min-value -64 --max-value 64python main.py uart --dry-run --input matrix/matrix_inputs.txt --expected matrix/matrix_expected.txt

    python main.py uart --port COM3 --baudrate 115200 --timeout 120 --read-counters
```
