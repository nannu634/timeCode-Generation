import re
import os
import sys
from pydub import AudioSegment
import os
import speech_recognition as sr


class ExtentionException(Exception):
    pass

class EmptyLabelException(Exception):
    pass


'''class Segment:
    """
    a unit of speech (i.e. phoneme, mora)
    """
    def __init__(self, tStart, tEnd, label):
        self.tStart = tStart
        self.tEnd = tEnd
        self.label = label

    def __add__(self, other):
        return Segment(self.tStart, other.tEnd, self.label + other.label)

    def can_follow(self, other):
        """
        return True if Segment self can follow Segment other in one mora,
        otherwise return False
        example: (other, self)
             True: ('s', 'a'), ('sh', 'i'), ('ky', 'o:'), ('t', 's')
             False: ('a', 'q'), ('a', 's'), ('u', 'e'), ('s', 'ha')
        """
        vowels = ['a', 'i', 'u', 'e', 'o', 'a:', 'i:', 'u:', 'e:', 'o:']
        consonants = ['w', 'r', 't', 'y', 'p', 's', 'd', 'f', 'g', 'h', 'j',
                      'k', 'z', 'c', 'b', 'n', 'm']
        only_consonants = lambda x: all([c in consonants for c in x])
        if only_consonants(other.label) and self.label in vowels:
            return True
        if only_consonants(other.label) and only_consonants(self.label):
            return True
        return False

    def to_textgrid_lines(self, segmentIndex):
        label = '' if self.label in ['silB', 'silE'] else self.label
        return [f'        intervals [{segmentIndex}]:',
                f'            xmin = {self.tStart} ',
                f'            xmax = {self.tEnd} ',
                f'            text = "{label}" ']

def read_lab(script_output_path, wav_file_path):
    # Load the audio file
    audio_path = os.path.abspath(wav_file_path)

    # Load the transcript (lab file content)
    with open(script_output_path, 'r', encoding='utf-8') as f:
        transcript = f.read()

    # Perform forced alignment with alignerwrapper
    aligner = PraatAligner()
    result = aligner.transcribe(transcript, audio_path)

    # Process the result to obtain time intervals for each segment
    segments = []
    for word in result['words']:
        tStart = word['start']
        tEnd = word['end']
        label = word['word'].strip()
        segments.append(Segment(tStart=tStart, tEnd=tEnd, label=label))

    return SegmentationLabel(segments)

    
class SegmentationLabel:
    """
    list of segments
    """
    def __init__(self, segments, separatedByMora=False):
        self.segments = segments
        self.separatedByMora = separatedByMora

    def by_moras(self):
        """
        return new SegmentationLabel object whose segment are moras 
        """
        if self.separatedByMora == True:
            return self

        moraSegments = []
        curMoraSegment = None
        for segment in self.segments:
            if curMoraSegment is None:
                curMoraSegment = segment
            elif segment.can_follow(curMoraSegment):
                curMoraSegment += segment
            else:
                moraSegments.append(curMoraSegment)
                curMoraSegment = segment
        if curMoraSegment:
            moraSegments.append(curMoraSegment)
        return SegmentationLabel(moraSegments, separatedByMora=True)

    def _textgrid_headers(self):
        segmentKind = 'mora' if self.separatedByMora else 'phoneme'
        return ['File type = "ooTextFile"',
                'Object class = "TextGrid"',
                ' ',
                'xmin = 0 ',
               f'xmax = {self.segments[-1].tEnd} ',
                'tiers? <exists> ',
                'size = 1 ',
                'item []: ',
                '    item [1]: ',
                '        class = "IntervalTier" ',
               f'        name = "{segmentKind}" ',
                '        xmin = 0 ',
               f'        xmax = {self.segments[-1].tEnd} ',
               f'        intervals: size = {len(self.segments)} ']

    def to_textgrid(self, textgridFileName):
        """
        save to .TextGrid file, which is available for Praat
        """
        try:
            if not self.segments:
                raise EmptyLabelException(f'warning: no label data found in '
                                          f'{textgridFileName}')
        except EmptyLabelException as e:
            print(e)
            return

        textgridLines = self._textgrid_headers()
        for i, segment in enumerate(self.segments):
            textgridLines.extend(segment.to_textgrid_lines(i + 1))
        with open(textgridFileName, 'w', encoding='utf-8') as f:
           f.write('\n'.join(textgridLines))'''


import gentle
from pydub import AudioSegment

def generate_textgrid_from_lab_and_wav(lab_file_path, wav_file_path, output_textgrid_path):
    # Load the lab file (assuming it's a simple text file with timestamped annotations)
    with open(lab_file_path, 'r', encoding='utf-8') as lab_file:
        lab_data = lab_file.readlines()

    # Extract text from lines between <s> tags
    text = ' '.join(line.strip() for line in lab_data if '<s>' not in line)

    # Load the audio file and resample to the required rate (e.g., 16000 Hz)
    audio = AudioSegment.from_wav(wav_file_path).set_frame_rate(16000)

    # Perform forced alignment
    aligner = gentle.ForcedAligner()
    result = aligner.transcribe(audio, text)

    # Extract aligned intervals
    intervals = [(word['start'], word['end'], word['alignedWord']) for word in result.words]

    # Create a TextGrid object
    textgrid = gentle.Textgrid()

    # Add each aligned interval to the TextGrid
    for start_time, end_time, label in intervals:
        textgrid.add_interval(gentle.Interval(start_time, end_time, label))

    # Save the TextGrid to a file
    textgrid.write(output_textgrid_path)





