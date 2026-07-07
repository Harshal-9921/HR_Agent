import os
import zipfile

def zipdir(path, ziph):
    for root, dirs, files in os.walk(path):
        # Exclude directories
        dirs[:] = [d for d in dirs if d not in ('node_modules', 'venv', 'venv_temp', '__pycache__', '.git', 'dist', 'redis', 'uploads')]
        for file in files:
            if not file.endswith('.pyc') and not file.endswith('.rdb'):
                filepath = os.path.join(root, file)
                ziph.write(filepath, os.path.relpath(filepath, path))

if __name__ == '__main__':
    with zipfile.ZipFile('deploy.zip', 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipdir('.', zipf)
    print("Created deploy.zip successfully!")
