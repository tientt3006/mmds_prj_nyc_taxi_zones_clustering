# Jupyter Notebooks cho NYC Taxi Graph Mining

## Setup

```bash
# Activate venv
cd ~/massive_data_mining
source ~/mmds-venv/bin/activate

# Install Jupyter
pip install jupyter ipykernel

# Start Jupyter
jupyter notebook --ip=0.0.0.0 --port=8888 --no-browser
```

## Access từ Windows

**Option 1: Direct access**
```
http://master:8888
```

**Option 2: SSH Tunnel**
```bash
# Trên Windows
ssh -L 8888:localhost:8888 tiennd@master

# Mở browser
http://localhost:8888
```

## Notebooks

### run_pipeline.ipynb
- Chạy toàn bộ pipeline từ đầu đến cuối
- Hiển thị kết quả từng bước
- Tạo visualizations inline
- **Runtime:** 3-5 giờ (full data)

### exploration.ipynb (tạo riêng nếu cần)
- Exploratory data analysis
- Test với sample data
- Quick prototyping

## Tips

1. **Chạy từng cell**: Ctrl+Enter
2. **Chạy và next**: Shift+Enter
3. **Stop kernel**: Kernel → Interrupt
4. **Restart**: Kernel → Restart & Clear Output

## Troubleshooting

**Kernel dies:**
```bash
# Tăng memory cho Jupyter
jupyter notebook --NotebookApp.max_buffer_size=1073741824
```

**Cannot connect:**
```bash
# Check firewall
sudo ufw allow 8888/tcp
```
