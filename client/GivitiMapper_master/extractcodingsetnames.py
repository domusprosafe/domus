import re
file = open('prosafecodification.txt', 'rb')
codifications = file.readlines()
file.close()
className = 'core.complCodification.'
output = open('prosafe.txt', 'a')
for line in codifications:
    try:
        m = re.search('name=\"([^\"]*)\"', line)
        codingSetValue = m.group(0).lstrip('name=').replace('"', '')
        output.write(className + codingSetValue + '\n')
    except:
        pass
output.close()