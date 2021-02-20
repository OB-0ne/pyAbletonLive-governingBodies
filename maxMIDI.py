from pythonosc.udp_client import SimpleUDPClient
from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import OSCUDPServer, AsyncIOOSCUDPServer
import asyncio

import time
import random
import mido

class communicateOSC():

    ip = "127.0.0.1"
    port_in = 6450
    port_out = 6451

    client_in = None
    client_out = None
    transport = None

    @classmethod
    async def create(cls,ip, port_in, port_out):
        self = communicateOSC()

        # setting the IP to localhost
        self.ip = ip

        # setting the in and out port
        self.port_in = port_in
        self.port_out = port_out

        # setting the object which sents messages out
        self.client_out = SimpleUDPClient(self.ip, self.port_out)
 
        # trying an async server
        self.client_in = AsyncIOOSCUDPServer((self.ip, self.port_in), self.configureDispatcher(), asyncio.get_event_loop())
        self.transport, _ = await self.client_in.create_serve_endpoint()  # Create datagram endpoint and start serving

        return self

    def closeNetwork(self):
        self.transport.close()

    def configureDispatcher(self):
        # setting the object which receives the messages and decides where to send them
        dispatcher = Dispatcher()
        dispatcher.map("/max/inputs/midi", self.playMIDI)
        dispatcher.set_default_handler(self.default_handler)

        return dispatcher

    def playMIDI(self,address, *args):

        out_port = mido.open_output('testMidi Port 1')

        print(args[0])

        # read the big midi
        midis = ['05','08','03']
        big_midi = mido.MidiFile()
        track = mido.MidiTrack()
        for i in midis:
            mid = mido.MidiFile(f'D:\SBU\\05 Music Composition\\12 MIDI RNN\\basicRNN-midi-governingBodies\outputs\heavyRain_e1250\heavyRain_{i}.mid')
            for m_track in mid.tracks:
                for msg in m_track:
                    track.append(msg)
        big_midi.tracks.append(track)

        # read and append multiple small midi
        midis = ['05','07','03']
        small_midi = mido.MidiFile()
        track = mido.MidiTrack()
        for i in midis:
            mid = mido.MidiFile(f'D:\SBU\\05 Music Composition\\12 MIDI RNN\\basicRNN-midi-governingBodies\outputs\heavyRain_Improv_e220\heavyRain_improv_{i}.mid')
            for m_track in mid.tracks:
                for msg in m_track:
                    track.append(msg)
        small_midi.tracks.append(track)

        # get the track bassy with lower MIDI notes
        bass_offset = 36
        for track in small_midi.tracks:
            for msg in track:
                if not msg.is_meta:
                    msg.note = msg.note - bass_offset

        # make both tracks on single midi
        big_midi.add_track('bass')
        big_midi.tracks[1] = small_midi.tracks[0]

        for msg in big_midi.tracks[0]:
            if not msg.is_meta:
                msg.channel = 0

        for msg in big_midi.tracks[1]:
            if not msg.is_meta:
                msg.channel = 1
                msg.time = msg.time*16

        # send it out to play
        for msg in big_midi.play():
                out_port.send(msg)

        out_port.close()

    def default_handler(self,address, *args):
        print(f"Unknown Input - {address}: {args}")


async def init_main():
    
    max_in = await communicateOSC.create('127.0.0.1', 6551, 6552)

    while True:
        await asyncio.sleep(1)

    max_in.closeNetwork()  # Clean up serve endpoint

asyncio.run(init_main())