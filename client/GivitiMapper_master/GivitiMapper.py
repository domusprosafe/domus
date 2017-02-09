import rdflib
import gc
from GivitiReasoner import GivitiReasoner

class GivitiMapper :

    inputDataNamespace = ""
    outputDataNamespace = ""

    def __init__ (self, inputDataNamespace, outputDataNamespace) :
        self.inputDataNamespace = inputDataNamespace
        self.outputDataNamespace = outputDataNamespace


    def doMapping (self, dataGraph, progressBar=None) :
        
        expandedGraph = rdflib.Graph()
        mappingGraph = self.getMappingGraph()

        expandedGraph += mappingGraph
        expandedGraph += dataGraph
        
        for ns in dataGraph.namespaces() :
            expandedGraph.bind(ns[0], ns[1])
        for ns in mappingGraph.namespaces() :
            expandedGraph.bind(ns[0], ns[1])
                
        #reasoner = RDFClosure.DeductiveClosure(RDFClosure.OWLRL_Semantics)
        #reasoner.expand(expandedGraph)
            
        reasoner = GivitiReasoner()
        expandedGraph = reasoner.closureOfInstancesProperties(expandedGraph,progressBar)
                
        dataNamespaces = [x[1] for x in dataGraph.namespaces()]
        mappingNamespaces = [x[1] for x in mappingGraph.namespaces()]
        outputNamespaces = [str(x) for x in dataNamespaces if x not in mappingNamespaces]
        outputNamespaces.append(self.getExtendedNamespace(self.outputDataNamespace))
        
        progressBar.Step(stepValue=1, message = 'filtering resulting graph')
        filteredGraph = self.filterGraphByNamespace(expandedGraph, outputNamespaces)
        progressBar.Step(stepValue=400, message = 'Filtering completed!')
        
        return filteredGraph


    def getMappingGraph (self) :
        
        from psconstants import abspath
        
        #path = 'file://' + abspath('GivitiMapper')
        path = './GivitiMapper'
        filename = path + '/' + self.inputDataNamespace + '_to_' + self.outputDataNamespace + '.ttl'
        
        g = rdflib.Graph()
        g.parse(filename, format='n3')
               
        filenameAuto = path + '/' + self.inputDataNamespace + '_to_' + self.outputDataNamespace + '_auto.ttl'
        
        gAuto = rdflib.Graph()
        gAuto.parse(filenameAuto, format='n3')
             
        # Merging namespaces 
        mappingGraph = g + gAuto
        for ns in g.namespaces() :
            mappingGraph.bind(ns[0], ns[1])
        for ns in gAuto.namespaces() :
            mappingGraph.bind(ns[0], ns[1])
 
        return mappingGraph


    def filterGraphByNamespace (self, graph, namespaces) :
        
        filteredGraph = rdflib.Graph()        
        
        for s, p, o in graph :
            pIsOk = False
            oIsOk = False

            if (type(o) is rdflib.term.Literal) or (type(o) is rdflib.term.BNode) :
                oIsOk = True
            else :
                for ns in namespaces :
                    if (o.startswith(ns)) :
                        oIsOk = True
            if not oIsOk :
                continue

            for ns in namespaces :
                if (p.startswith(ns)) :
                    filteredGraph.add((s, p, o))
                    break
                

        for ns in graph.namespaces() :
            filteredGraph.bind(ns[0], ns[1])

        return filteredGraph        

    
    def getExtendedNamespace(self, namespace) :
        return "http://giviti.marionegri.it/knowledgebase/" + namespace + "#"


    def mapDataFromFile (self, filename) :
       
        g = rdflib.Graph()
        g.parse(filename, format='n3')
        
        resultingGraph = self.doMapping(g)
        
        gc.collect()

        return resultingGraph
        


if __name__ == "__main__" :

    mapper = GivitiMapper("prosafe-core4", "prosafe-core3")
    
    resultingGraph = mapper.mapDataFromFile("input3.ttl")
    
    s = resultingGraph.serialize(format = "turtle")
    f = open("output.ttl", "w")
    f.write(s)
    f.close()

