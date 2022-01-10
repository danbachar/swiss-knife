import os
from PIL import Image
def generate_bmp():
    datasets = [(1000,1000),(5000,5000),(15000,15000)] #ratio 25, 225
    f_names = ["small", "medium", "large"] 
    for idx in range(3):
        img = Image.new( 'RGB', datasets[idx], "black") # Create a new black image
        pixels = img.load() # Create the pixel map
        for i in range(img.size[0]):    # For every pixel:
            for j in range(img.size[1]):
                pixels[i,j] = (i, j, 100)
        img.save(f"{f_names[idx]}.bmp")
        print(f"Test image {f_names[idx]}.bmp is generated", flush=True)

def generate_text():
    f_name = ["dickens-20M.txt","dickens-100M.txt","dickens-200M.txt"]
    repeatTime = [5,2]
    for base_file in range(2):
        for _ in range(repeatTime[base_file]):
            with open(f_name[base_file]) as f:
                with open(f_name[base_file+1], "a") as f1:
                    for line in f:
                        f1.write(line)
        print(f"Test text {f_name[base_file+1]} is generated", flush=True)

def main():
    os.chdir('/root/dataset/')
    generate_bmp()
    generate_text()

if __name__ == '__main__':
    main()
