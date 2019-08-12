import  watermark_image
import  watermark_video
import  watermark_audio

def watermark(type,operation,input_file,watermark=""):
    function_name = 'watermark_%s.%s' % (type,operation)
    if operation=='embed':
        eval(function_name)(input_file,watermark)
    elif operation=='extract':
        return eval(function_name)(input_file)
    else:
        print("Please input the correct operation(embed or extract?)")

