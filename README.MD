# Chạy project
puthon run.py

# Xóa môi trường Conda cũ

conda remove --name flask-crawler --all

# Tạo môi trường

conda env create -f conda-env.yml

# Kích hoạt môi trường

conda init
conda activate flask-crawler

# Hủy kích hoạt

conda deactivate
