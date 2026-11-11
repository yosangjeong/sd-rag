package javax.xml.bind;

/**
 * Minimal stand-in for the JAXB class removed from the JDK in Java 11.
 * hwplib imports it for a single base64 helper (HWPReader.fromBase64String),
 * which the HWP -> HWPX path never calls; this keeps the library unmodified.
 */
public final class DatatypeConverter {
    private DatatypeConverter() {}

    public static byte[] parseBase64Binary(String s) {
        return java.util.Base64.getMimeDecoder().decode(s);
    }
}
