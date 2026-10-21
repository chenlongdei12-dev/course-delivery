import Foundation
import AVFoundation
import AppKit

func value(_ flag:String)->String? { guard let i=CommandLine.arguments.firstIndex(of:flag), i+1<CommandLine.arguments.count else{return nil}; return CommandLine.arguments[i+1] }
guard let inputPath=value("--input"), let outputPath=value("--output") else { fatalError("Usage: swift analyze_video.swift --input /path/video.mp4 --output /path/analysis [--sample-times 0,10,60]") }
let input=URL(fileURLWithPath:inputPath), out=URL(fileURLWithPath:outputPath,isDirectory:true)
try FileManager.default.createDirectory(at:out,withIntermediateDirectories:true)
let asset=AVURLAsset(url:input), duration=try await asset.load(.duration).seconds
guard let vt=try await asset.loadTracks(withMediaType:.video).first, let at=try await asset.loadTracks(withMediaType:.audio).first else { fatalError("Video and audio tracks are required") }
let size=try await vt.load(.naturalSize), fps=try await vt.load(.nominalFrameRate)
let reader=try AVAssetReader(asset:asset)
let audioOut=AVAssetReaderTrackOutput(track:at,outputSettings:[AVFormatIDKey:kAudioFormatLinearPCM,AVLinearPCMIsFloatKey:true,AVLinearPCMBitDepthKey:32,AVLinearPCMIsNonInterleaved:false])
reader.add(audioOut); reader.startReading(); var bins:[Int:(Double,Int)]=[:]
while let sample=audioOut.copyNextSampleBuffer() {
 let pts=CMSampleBufferGetPresentationTimeStamp(sample).seconds
 guard let block=CMSampleBufferGetDataBuffer(sample) else{continue}; let n=CMBlockBufferGetDataLength(block); var bytes=[UInt8](repeating:0,count:n)
 CMBlockBufferCopyDataBytes(block,atOffset:0,dataLength:n,destination:&bytes)
 bytes.withUnsafeBytes { raw in let vals=raw.bindMemory(to:Float.self); var sum=0.0; for v in vals {sum += Double(v)*Double(v)}; let k=Int(floor(pts)); let old=bins[k] ?? (0,0); bins[k]=(old.0+sum,old.1+vals.count) }
}
var csv="second,rms_db\n"; var levels:[Int:Double]=[:]
for k in bins.keys.sorted(){let x=bins[k]!; let db=20*log10(max(sqrt(x.0/Double(max(x.1,1))),1e-12)); levels[k]=db; csv += "\(k),\(String(format:"%.2f",db))\n"}
try csv.write(to:out.appendingPathComponent("audio_rms_1s.csv"),atomically:true,encoding:.utf8)
var sustained:Int?=nil
for start in 0...max(0,Int(duration)-10) { if (start..<start+10).filter({(levels[$0] ?? -120) > -50}).count >= 5 {sustained=start;break} }
var samples=[0.0,5,10,30,60]; if let s=value("--sample-times") {samples=s.split(separator:",").compactMap{Double($0)}}
let gen=AVAssetImageGenerator(asset:asset); gen.appliesPreferredTrackTransform=true; gen.maximumSize=CGSize(width:1280,height:720)
for sec in samples where sec>=0 && sec<duration { let (cg,_)=try await gen.image(at:CMTime(seconds:sec,preferredTimescale:600)); let png=NSBitmapImageRep(cgImage:cg).representation(using:.png,properties:[:])!; try png.write(to:out.appendingPathComponent(String(format:"frame_%08.3f.png",sec))) }
let metadata:[String:Any]=["source":input.path,"duration_sec":duration,"width":size.width,"height":size.height,"nominal_fps":fps,"video_tracks":1,"audio_tracks":1,"first_sustained_audio_candidate_sec":sustained as Any,"sustained_rule":"at least 5 of 10 one-second bins above -50 dB; confirm visually and semantically"]
try JSONSerialization.data(withJSONObject:metadata,options:[.prettyPrinted,.sortedKeys]).write(to:out.appendingPathComponent("metadata.json"))
print(String(data:try JSONSerialization.data(withJSONObject:metadata,options:[.sortedKeys]),encoding:.utf8)!)
