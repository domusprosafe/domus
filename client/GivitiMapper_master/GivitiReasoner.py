import rdflib
import rdfextras

rdflib.plugin.register('sparql', rdflib.query.Processor, 'rdfextras.sparql.processor', 'Processor')
rdflib.plugin.register('sparql', rdflib.query.Result, 'rdfextras.sparql.query', 'SPARQLQueryResult')

class GivitiReasoner :

    def __init__ (self) :
        pass
    
    def executeRule(self, ruleName, graph):
        
        path = './GivitiMapper'
        file_name = path + '/' + "%s.sparql" % ruleName
        f = open(file_name)
        q = f.read()
        f.close()
        result = graph.query(q)

        return result.graph
        
    def closureOfInstancesProperties(self, graph, progressBar=None) :
        result = rdflib.Graph()
        result += graph
        
        dic_file = {
        1:'eq-sym',
        2:'eq-trans',
        3:'prp-eqp1',
        4:'prp-eqp2',
        5:'eq-rep-o',
        6:'scm-eqc1',
        7:'scm-eqc2',
        8:'cls-hv2',
        10:'cax-eqc1',
        11:'cax-eqc2',
        12:'cls-hv1'}
        
        from mainlogic import _
        for el in sorted(dic_file.keys()):
            progressBar.Step(stepValue=(1.0 / 11.0), message = _('executing rules:') + ' %s' % dic_file[el], isRule=True)
            tempGraph = self.executeRule(dic_file[el], result)
            result += tempGraph
        
        for ns in graph.namespaces() :
            result.bind(ns[0], ns[1])

        return result

if __name__ == "__main__" :
    reasoner = GivitiReasoner()
    g = rdflib.Graph()
    g.parse("prova.ttl", format="turtle")
    result = reasoner.closureOfInstancesProperties(g)
    
    for t in result :
        print t


