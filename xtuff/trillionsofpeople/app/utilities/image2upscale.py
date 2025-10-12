import argparse
import os
import subprocess

def upscale_this_image(imagename, output_path="output/rescaled/rescaled.png"):
    # run realesgran via subprocess
    #un_me = [ "/Users/fred/unity/app/utilities/realesrgan-ncnn-vulkan-20220424-macos/realesrgan-ncnn-vulkan", "-iv", "output/democratic_weaponization_weaponization/weaponization.png", "-o", "output.png"]
    os.chdir("/Users/fred/unity/app/utilities/realesrgan-ncnn-vulkan-20220424-macos")
    result = subprocess.run([ "./realesrgan-ncnn-vulkan", "-i", imagename, "-o", output_path])
    return result

if __name__ == "__main__":

    argparser = argparse.ArgumentParser()
    argparser.add_argument("--imagename", "-I", type=str, default="output/democratic_weaponization_weaponization/weaponization.png")
    argparser.add_argument("--output_path", "-O", type=str, default="output/rescaled/rescaled.png")
    args = argparser.parse_args()
    imagename = args.imagename
    output_path = args.output_path
    result = upscale_this_image(imagename, output_path)
    print(result)


