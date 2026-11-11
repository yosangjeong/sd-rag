import kr.dogfoot.hwp2hwpx.Hwp2Hwpx;
import kr.dogfoot.hwplib.object.HWPFile;
import kr.dogfoot.hwplib.reader.HWPReader;
import kr.dogfoot.hwpxlib.object.HWPXFile;
import kr.dogfoot.hwpxlib.writer.HWPXWriter;

/**
 * Convert HWP 5.x files to HWPX, following the usage in the hwp2hwpx README.
 * Usage: java Convert in1.hwp out1.hwpx [in2.hwp out2.hwpx ...]
 * Several pairs per call so one JVM start serves all annexes of a statute.
 */
public class Convert {
    public static void main(String[] args) throws Exception {
        if (args.length == 0 || args.length % 2 != 0) {
            System.err.println("usage: java Convert in.hwp out.hwpx [in.hwp out.hwpx ...]");
            System.exit(2);
        }
        for (int i = 0; i < args.length; i += 2) {
            HWPFile from = HWPReader.fromFile(args[i]);
            HWPXFile to = Hwp2Hwpx.toHWPX(from);
            HWPXWriter.toFilepath(to, args[i + 1]);
            System.out.println("ok " + args[i + 1]);
        }
    }
}
