
all_ads = []

for page in range(1, 4):
    ads = [page * 10, page * 10 + 1]

    all_ads.extend(ads)

print(all_ads)
