#!/usr/bin/env python
import ROOT
import array
import os
from Jet import Jet

# propagate JES/JER systematics from jets to higgs candidate dijet pair 
class HiggsCandidateSystematics(object):
    
    def __init__(self, addSystematics=True, tagidx="", prefix="H"):
        self.debug = 'XBBDEBUG' in os.environ
        self.lastEntry = -1
        self.nJet = -1
        self.nJetMax = 100
        self.branches = []
        self.branchBuffers = {}
        self.addSystematics = addSystematics
        self.tagidx = tagidx
        self.prefix = prefix

        self.jetSystematics = ['jer','jesAbsoluteStat','jesAbsoluteScale','jesAbsoluteFlavMap','jesAbsoluteMPFBias','jesFragmentation','jesSinglePionECAL','jesSinglePionHCAL','jesFlavorQCD','jesRelativeJEREC1','jesRelativeJEREC2','jesRelativeJERHF','jesRelativePtBB','jesRelativePtEC1','jesRelativePtEC2','jesRelativePtHF','jesRelativeBal','jesRelativeFSR','jesRelativeStatFSR','jesRelativeStatEC','jesRelativeStatHF','jesPileUpDataMC','jesPileUpPtRef','jesPileUpPtBB','jesPileUpPtEC1','jesPileUpPtEC2','jesPileUpPtHF','jesPileUpMuZero','jesPileUpEnvelope','jesTotal']

        # corrected dijet (Higgs candidate) properties
        self.higgsProperties = [self.prefix + '_' + x for x in ['pt','eta', 'phi', 'mass']]

        if self.debug:
            print "DEBUG: HiggsCandidateSystematics::__init__(), with idx=", self.tagidx, " prefix=", self.prefix

    def customInit(self, initVars):
        self.sample = initVars['sample']
        self.higgsPropertiesWithSys = self.higgsProperties if self.sample.type != 'DATA' else []
        for higgsProperty in self.higgsProperties: 
            self.branchBuffers[higgsProperty] = array.array('f', [0.0])
            self.branches.append({'name': higgsProperty, 'formula': self.getBranch, 'arguments': higgsProperty})
            # for data only include the min/max (set to nominal) to simplify cutting
            systList = self.jetSystematics + ['minmax'] if higgsProperty in self.higgsPropertiesWithSys else ['minmax']
            for syst in systList:
                for Q in ['Up', 'Down']:
                    higgsPropertySyst = "{p}_{s}_{q}".format(p=higgsProperty, s=syst, q=Q)
                    self.branchBuffers[higgsPropertySyst] = array.array('f', [0.0])
                    self.branches.append({'name': higgsPropertySyst, 'formula': self.getBranch, 'arguments': higgsPropertySyst})

        for p in ['Jet_pt_minmax', 'Jet_mass_minmax']:
            for q in ['Up', 'Down']:
                self.branchBuffers[p+q] = array.array('f', [0.0]*self.nJetMax)
                self.branches.append({'name': p+q, 'formula': self.getVectorBranch, 'arguments': {'branch': p+q}, 'length': self.nJetMax, 'leaflist': p+q+'[nJet]/F'})

    def getBranches(self):
        return self.branches
 
    # read from buffers which have been filled in processEvent()    
    def getBranch(self, event, arguments=None):
        self.processEvent(event)
        if arguments:
            return self.branchBuffers[arguments][0]
    
    # read from buffers which have been filled in processEvent()    
    def getVectorBranch(self, event, arguments=None, destinationArray=None):
        self.processEvent(event)
        length = min(self.nJet, self.nJetMax)
        destinationArray[:length] = self.branchBuffers[arguments['branch']][:length]
        #for i in range(length):
        #    destinationArray[i] = self.branchBuffers[arguments['branch']][i]

    def processEvent(self, tree):
        currentEntry = tree.GetReadEntry()
        # if current entry has not been processed yet
        if currentEntry != self.lastEntry:
            self.lastEntry = currentEntry

            # idx passed as an argument
            if self.tagidx:
                #print "Using the {idx}".format(idx=self.tagidx)
                hJidx0 = getattr(tree,self.tagidx)[0] 
                hJidx1 = getattr(tree,self.tagidx)[1]
                #print "tag0 {t0} and tag1 {t1}".format(t0=hJidx0,t1=hJidx1) 
            else:
                print "Missing bTag index. Check general.ini"
                raise Exception("bTagIndexNotSpecified")

            # select branches from tree
            # for 2016 nano v5
            treeJet_PtReg = tree.Jet_PtReg 
            treeJet_pt = tree.Jet_pt
            treeJet_Pt = tree.Jet_Pt
            treeJet_bReg = tree.Jet_bReg

            #treeJet_Pt = tree.Jet_Pt
            treeJet_phi = tree.Jet_phi
            treeJet_eta = tree.Jet_eta

            if self.sample.type != 'DATA':
                treeJet_mass = tree.Jet_mass_nom
            else:
                treeJet_mass = tree.Jet_mass

            # nominal value
            hJ0 = ROOT.TLorentzVector()
            hJ1 = ROOT.TLorentzVector()

            hJ0.SetPtEtaPhiM(treeJet_PtReg[hJidx0],treeJet_eta[hJidx0],treeJet_phi[hJidx0],treeJet_mass[hJidx0] * treeJet_bReg[hJidx0])
            hJ1.SetPtEtaPhiM(treeJet_PtReg[hJidx1],treeJet_eta[hJidx1],treeJet_phi[hJidx1],treeJet_mass[hJidx1] * treeJet_bReg[hJidx1])
            #hJ0.SetPtEtaPhiM(treeJet_bReg[hJidx0]*treeJet_Pt[hJidx0]/treeJet_pt[hJidx0],treeJet_eta[hJidx0],treeJet_phi[hJidx0],treeJet_mass[hJidx0] * treeJet_bReg[hJidx0]/treeJet_pt[hJidx0])
            #hJ1.SetPtEtaPhiM(treeJet_bReg[hJidx1]*treeJet_Pt[hJidx1]/treeJet_pt[hJidx1],treeJet_eta[hJidx1],treeJet_phi[hJidx1],treeJet_mass[hJidx1] * treeJet_bReg[hJidx1]/treeJet_pt[hJidx1])

            dijet_Nominal = hJ0 + hJ1

            self.branchBuffers[self.prefix + '_pt'][0] = dijet_Nominal.Pt()
            self.branchBuffers[self.prefix + '_eta'][0] = dijet_Nominal.Eta()
            self.branchBuffers[self.prefix + '_phi'][0] = dijet_Nominal.Phi()
            self.branchBuffers[self.prefix + '_mass'][0] = dijet_Nominal.M()

            # systematics
            valueList = {x:[self.branchBuffers[x][0]] for x in self.higgsProperties}
            if self.addSystematics and self.sample.type != 'DATA':
                for syst in self.jetSystematics:
                    for Q in ['Up', 'Down']:
                        if self.sample.type != 'DATA':
                            hJ0 = ROOT.TLorentzVector()
                            hJ1 = ROOT.TLorentzVector()

                            hJ0.SetPtEtaPhiM(treeJet_PtReg[hJidx0]*getattr(tree, 'Jet_pt_{s}{d}'.format(s=syst, d=Q))[hJidx0]/treeJet_Pt[hJidx0],treeJet_eta[hJidx0],treeJet_phi[hJidx0],getattr(tree, 'Jet_mass_{s}{d}'.format(s=syst, d=Q))[hJidx0] * treeJet_bReg[hJidx0])
                            hJ1.SetPtEtaPhiM(treeJet_PtReg[hJidx1]*getattr(tree, 'Jet_pt_{s}{d}'.format(s=syst, d=Q))[hJidx1]/treeJet_Pt[hJidx1],treeJet_eta[hJidx1],treeJet_phi[hJidx1],getattr(tree, 'Jet_mass_{s}{d}'.format(s=syst, d=Q))[hJidx1] * treeJet_bReg[hJidx1])
                            #dummy
                            #hJ0.SetPtEtaPhiM(treeJet_bReg[hJidx0]*getattr(tree, 'Jet_pt_{s}{d}'.format(s=syst, d=Q))[hJidx0]/treeJet_pt[hJidx0],treeJet_eta[hJidx0],treeJet_phi[hJidx0],getattr(tree, 'Jet_mass_{s}{d}'.format(s=syst, d=Q))[hJidx0] * treeJet_bReg[hJidx0]/treeJet_pt[hJidx0])
                            #hJ1.SetPtEtaPhiM(treeJet_bReg[hJidx1]*getattr(tree, 'Jet_pt_{s}{d}'.format(s=syst, d=Q))[hJidx1]/treeJet_pt[hJidx1],treeJet_eta[hJidx1],treeJet_phi[hJidx1],getattr(tree, 'Jet_mass_{s}{d}'.format(s=syst, d=Q))[hJidx1] * treeJet_bReg[hJidx1]/treeJet_pt[hJidx1])
                            dijet = hJ0 + hJ1
                        else:
                            dijet = dijet_Nominal

                        self.branchBuffers[self.prefix + '_pt_{s}_{d}'.format(s=syst, d=Q)][0] = dijet.Pt()
                        self.branchBuffers[self.prefix + '_eta_{s}_{d}'.format(s=syst, d=Q)][0] = dijet.Eta()
                        self.branchBuffers[self.prefix + '_phi_{s}_{d}'.format(s=syst, d=Q)][0] = dijet.Phi()
                        self.branchBuffers[self.prefix + '_mass_{s}_{d}'.format(s=syst, d=Q)][0] = dijet.M()

                        valueList[self.prefix + '_pt'].append(dijet.Pt())
                        valueList[self.prefix + '_eta'].append(dijet.Eta())
                        valueList[self.prefix + '_phi'].append(dijet.Phi())
                        valueList[self.prefix + '_mass'].append(dijet.M())

            # get minimum and maximum variation
            for syst in ['minmax']:
                for Q in ['Up', 'Down']:
                    for p in self.higgsProperties:
                        self.branchBuffers['{p}_{s}_{d}'.format(p=p, s=syst, d=Q)][0] = min(valueList[p]) if Q=='Down' else max(valueList[p])

            # min/max variations for Jet pt/mass
            self.nJet = tree.nJet
            treeJet_mass_sys = {}
            treeJet_pt_sys = {}
            if self.addSystematics and self.sample.type != 'DATA':
                # read all the arrays once to avoid getattr in the loop over the jets
                for syst in self.jetSystematics:
                    for Q in ['Up', 'Down']:
                        treeJet_mass_sys[syst+Q] = getattr(tree, 'Jet_mass_{s}{d}'.format(s=syst, d=Q))
                        treeJet_pt_sys[syst+Q] = getattr(tree, 'Jet_pt_{s}{d}'.format(s=syst, d=Q)) 

            # compute min/max for each jet
            for i in range(min(self.nJet, self.nJetMax)):
                ptList = [treeJet_Pt[i]]
                massList = [treeJet_mass[i]]
                if self.addSystematics and self.sample.type != 'DATA':
                    for syst in self.jetSystematics:
                        for Q in ['Up', 'Down']:
                            ptList.append(treeJet_pt_sys[syst+Q][i])
                            massList.append(treeJet_mass_sys[syst+Q][i])


                # compute maximum/minimum
                self.branchBuffers['Jet_pt_minmaxUp'][i] = max(ptList)
                self.branchBuffers['Jet_pt_minmaxDown'][i] = min(ptList)
                self.branchBuffers['Jet_mass_minmaxUp'][i] = max(massList)
                self.branchBuffers['Jet_mass_minmaxDown'][i] = min(massList)

        return True

