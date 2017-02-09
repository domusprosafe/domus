from httpagent import HTTPAgentClient
import unittest
import cProfile


class HTTPAgentClientTest(unittest.TestCase):
    
    def setUp(self):
        self.agent = HTTPAgentClient('http://localhost:8080/', 'validKey', 'validPass')
        
    ## def testDelete(self):
              
        ## #ELIMINO di tutti i record
        ## self.agent.addQuery('DELETE FROM prova')
        ## outMsg =  self.agent.sendQuery()
        ## self.agent.clearQuery()

    def testInsert50(self):
        for i in ['A', 'B', 'C', 'D', 'E']:
            for k in range(0,10):
                self.agent.addQuery("INSERT INTO prova(name, value) VALUES('%s', %d)" % (i, k))
        
        outMsg =  self.agent.sendQuery()
        
        
    ## def testInsert500(self):
        ## for i in ['A', 'B', 'C', 'D', 'E']:
            ## for k in range(0,100):
                ## self.agent.addQuery("INSERT INTO prova(name, value) VALUES('%s', %d)" % (i, k))
        
        ## outMsg =  self.agent.sendQuery()
        ## self.agent.clearQuery()
        
    def testInsert1000(self):
        for i in ['A', 'B', 'C', 'D', 'E']:
            for k in range(0,200):
                
                self.agent.addQuery("INSERT INTO prova(name, value) VALUES('%s', %d);" % (i, k))
        
        outMsg =  self.agent.sendQuery()
        
    
    ## def testInsert10000(self):
        ## self.agent.addQuery("BEGIN;")
        ## for i in ['A', 'B', 'C', 'D', 'E']:
            ## for k in range(0,2000):
                
                ## self.agent.addQuery("INSERT INTO prova(name, value) VALUES('%s', %d);" % (i, k))
        ## self.agent.addQuery("COMMIT;")
        ## outMsg =  self.agent.sendQuery()
        ## self.agent.clearQuery()
        
                
    def testSelect1000(self):
              
        #selezione di tutti i record
        self.agent.addQuery('SELECT * FROM prova LIMIT 1000')
        outMsg =  self.agent.sendQuery()
        print outMsg.data[0][:100]
       
        

def testIt():
    suite = unittest.TestLoader().loadTestsFromTestCase(HTTPAgentClientTest)
    unittest.TextTestRunner(verbosity=2).run(suite)


if __name__ == '__main__':
    cProfile.run('testIt()')