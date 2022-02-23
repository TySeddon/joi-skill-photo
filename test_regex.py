import re

stars = re.findall(r'[\*]+',"Beach, Lori, ***")
if stars:
    print(stars[0])
