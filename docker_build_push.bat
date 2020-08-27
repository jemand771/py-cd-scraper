docker build -t jemand771/cd-scraper .
docker build -t jemand771/cd-scraper-discord -f Dockerfile-discord .

echo done building, press any key to push the images
pause

docker push jemand771/cd-scraper
docker push jemand771/cd-scraper-discord

echo done pushing, press any key to exit
pause