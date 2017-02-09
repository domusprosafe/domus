prosafeClassName = 'core_comorbidities_value'
m2ClassName = 'patologieCoesistenti_patologiecoesistentivalore'

nodeID = 1000
templateString = """
_:mapping%d a owl:Class;
     owl:equivalentClass
          [ a owl:Restriction ;
            owl:onProperty prosafe-core3:%s ;
            owl:hasValue prosafe-core3:%s ;
          ] ,
          [ a owl:Restriction ;
            owl:onProperty m2:%s ;
            owl:hasValue "%s" ;
          ] . 

"""

m2List = open('m2.txt', 'rb')
m2Lines = m2List.readlines()
m2List.close()
prosafeList = open('prosafe.txt', 'rb')
prosafeLines = prosafeList.readlines()
prosafeList.close()
output = open('output.txt', 'w')
for variable in range(len(prosafeLines)):
    m2Value = m2Lines[variable].replace('\r\n', '')
    prosafeValue = prosafeLines[variable]
    output.write(templateString % (nodeID, prosafeClassName, prosafeValue, m2ClassName, m2Value))
    nodeID = nodeID + 1
   
output.close()