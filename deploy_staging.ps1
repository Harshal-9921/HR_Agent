Write-Host "Creating deployment zip..."
python zip_project.py

Write-Host "Freeing up space on the server before upload..."
ssh uadmin@10.130.37.2 "echo 'Propalms@123' | sudo -S docker system prune -a -f --volumes && echo 'Propalms@123' | sudo -S docker builder prune -a -f"

Write-Host "Uploading project to staging server..."
scp deploy.zip uadmin@10.130.37.2:/home/uadmin/

Write-Host "Connecting to server to deploy..."
ssh uadmin@10.130.37.2 "mkdir -p HR_Agent && python3 -m zipfile -e deploy.zip HR_Agent && cd HR_Agent && (echo 'Propalms@123' | sudo -S docker compose up -d --build || echo 'Propalms@123' | sudo -S docker-compose up -d --build)"

Write-Host "Deployment finished!"
