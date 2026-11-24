package br.unifor.distribuidos.soap;

import br.unifor.distribuidos.common.exception.ResourceNotFoundException;
import br.unifor.distribuidos.common.exception.ValidationException;
import br.unifor.distribuidos.common.model.Musica;
import br.unifor.distribuidos.common.model.Playlist;
import br.unifor.distribuidos.common.model.Usuario;
import br.unifor.distribuidos.common.service.StreamingService;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;
import org.w3c.dom.NodeList;
import org.xml.sax.InputSource;

import javax.xml.parsers.DocumentBuilderFactory;
import java.io.IOException;
import java.io.StringReader;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.function.Function;

/**
 * Entrega Java 2: API SOAP/XML com WSDL delegando ao núcleo StreamingService.
 */
@RestController
public class StreamingSoapController {
    private static final String SOAP_ENV_NS = "http://schemas.xmlsoap.org/soap/envelope/";
    private static final String TNS = "http://unifor.br/distribuidos/streaming";

    private final StreamingService service;
    private final Map<String, Function<Element, String>> handlers;

    public StreamingSoapController(StreamingService service) {
        this.service = service;
        this.handlers = Map.ofEntries(
                Map.entry("ListarUsuariosRequest", this::opListarUsuarios),
                Map.entry("ObterUsuarioRequest", this::opObterUsuario),
                Map.entry("CriarUsuarioRequest", this::opCriarUsuario),
                Map.entry("AtualizarUsuarioRequest", this::opAtualizarUsuario),
                Map.entry("RemoverUsuarioRequest", this::opRemoverUsuario),
                Map.entry("ListarMusicasRequest", this::opListarMusicas),
                Map.entry("ObterMusicaRequest", this::opObterMusica),
                Map.entry("CriarMusicaRequest", this::opCriarMusica),
                Map.entry("AtualizarMusicaRequest", this::opAtualizarMusica),
                Map.entry("RemoverMusicaRequest", this::opRemoverMusica),
                Map.entry("ListarPlaylistsRequest", this::opListarPlaylists),
                Map.entry("ObterPlaylistRequest", this::opObterPlaylist),
                Map.entry("CriarPlaylistRequest", this::opCriarPlaylist),
                Map.entry("AtualizarPlaylistRequest", this::opAtualizarPlaylist),
                Map.entry("RemoverPlaylistRequest", this::opRemoverPlaylist),
                Map.entry("AdicionarMusicaNaPlaylistRequest", this::opAdicionarMusicaNaPlaylist),
                Map.entry("RemoverMusicaDaPlaylistRequest", this::opRemoverMusicaDaPlaylist),
                Map.entry("ListarPlaylistsPorUsuarioRequest", this::opListarPlaylistsPorUsuario),
                Map.entry("ListarMusicasPorPlaylistRequest", this::opListarMusicasPorPlaylist),
                Map.entry("ListarPlaylistsPorMusicaRequest", this::opListarPlaylistsPorMusica)
        );
    }

    @GetMapping(value = "/", produces = MediaType.TEXT_HTML_VALUE)
    public ResponseEntity<String> playground() throws IOException {
        Path resolved = resolveSoapContractFile("SOAP_PLAYGROUND_PATH", "playground.html");
        if (resolved == null) {
            return ResponseEntity.status(HttpStatus.NOT_FOUND)
                    .contentType(MediaType.TEXT_PLAIN)
                    .body("SOAP playground nao encontrado.");
        }
        String html = Files.readString(resolved).replace("{{SERVICE_LABEL}}", "Java SOAP (Spring Boot)");
        return ResponseEntity.ok()
                .contentType(MediaType.parseMediaType("text/html;charset=UTF-8"))
                .body(html);
    }

    @GetMapping("/health")
    public Map<String, Object> health() {
        return service.healthCheck();
    }

    @GetMapping("/soap")
    public ResponseEntity<String> getWsdl(@RequestParam(required = false) String wsdl) throws IOException {
        if (wsdl != null) {
            Path resolved = resolveSoapContractFile("WSDL_PATH", "streaming.wsdl");
            if (resolved != null) {
                return ResponseEntity.ok()
                        .contentType(MediaType.TEXT_XML)
                        .body(Files.readString(resolved));
            }
        }
        return ResponseEntity.ok()
                .contentType(MediaType.TEXT_PLAIN)
                .body("Use POST /soap ou GET /soap?wsdl");
    }

    @PostMapping(value = "/soap", consumes = {MediaType.TEXT_XML_VALUE, MediaType.APPLICATION_XML_VALUE, MediaType.ALL_VALUE}, produces = "text/xml;charset=UTF-8")
    public ResponseEntity<String> soapEndpoint(@RequestBody String rawXml) {
        try {
            DocumentBuilderFactory factory = DocumentBuilderFactory.newInstance();
            factory.setNamespaceAware(true);
            factory.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
            Document doc = factory.newDocumentBuilder().parse(new InputSource(new StringReader(rawXml)));

            Element body = findFirstChildByLocalName(doc.getDocumentElement(), "Body");
            if (body == null) {
                return faultResponse("soapenv:Client", "Corpo SOAP ausente.", HttpStatus.BAD_REQUEST);
            }
            Element opNode = firstElementChild(body);
            if (opNode == null) {
                return faultResponse("soapenv:Client", "Operação SOAP ausente.", HttpStatus.BAD_REQUEST);
            }

            String opName = localName(opNode);
            Function<Element, String> handler = handlers.get(opName);
            if (handler == null) {
                return faultResponse("soapenv:Client", "Operação SOAP desconhecida: " + opName, HttpStatus.BAD_REQUEST);
            }

            return ResponseEntity.ok()
                    .contentType(MediaType.parseMediaType("text/xml;charset=UTF-8"))
                    .body(wrapEnvelope(handler.apply(opNode)));
        } catch (ResourceNotFoundException ex) {
            return faultResponse("soapenv:Client", ex.getMessage(), HttpStatus.NOT_FOUND);
        } catch (ValidationException ex) {
            return faultResponse("soapenv:Client", ex.getMessage(), HttpStatus.BAD_REQUEST);
        } catch (Exception ex) {
            return faultResponse("soapenv:Client", "Erro ao processar XML SOAP: " + ex.getMessage(), HttpStatus.BAD_REQUEST);
        }
    }

    private String opListarUsuarios(Element req) {
        StringBuilder sb = new StringBuilder("<tns:ListarUsuariosResponse>");
        for (Usuario u : service.listarUsuarios()) {
            appendUsuario(sb, u);
        }
        return sb.append("</tns:ListarUsuariosResponse>").toString();
    }

    private String opObterUsuario(Element req) {
        Usuario u = service.obterUsuario(childText(req, "id", ""));
        StringBuilder sb = new StringBuilder("<tns:ObterUsuarioResponse>");
        appendUsuario(sb, u);
        return sb.append("</tns:ObterUsuarioResponse>").toString();
    }

    private String opCriarUsuario(Element req) {
        Usuario u = service.criarUsuario(
                childText(req, "nome", ""),
                Integer.parseInt(childText(req, "idade", "0")),
                childText(req, "id", null)
        );
        StringBuilder sb = new StringBuilder("<tns:CriarUsuarioResponse>");
        appendUsuario(sb, u);
        return sb.append("</tns:CriarUsuarioResponse>").toString();
    }

    private String opAtualizarUsuario(Element req) {
        Usuario u = service.atualizarUsuario(
                childText(req, "id", ""),
                childText(req, "nome", ""),
                Integer.parseInt(childText(req, "idade", "0"))
        );
        StringBuilder sb = new StringBuilder("<tns:AtualizarUsuarioResponse>");
        appendUsuario(sb, u);
        return sb.append("</tns:AtualizarUsuarioResponse>").toString();
    }

    private String opRemoverUsuario(Element req) {
        boolean ok = service.removerUsuario(childText(req, "id", ""));
        return "<tns:RemoverUsuarioResponse><tns:sucesso>" + ok + "</tns:sucesso></tns:RemoverUsuarioResponse>";
    }

    private String opListarMusicas(Element req) {
        StringBuilder sb = new StringBuilder("<tns:ListarMusicasResponse>");
        for (Musica m : service.listarMusicas()) {
            appendMusica(sb, m);
        }
        return sb.append("</tns:ListarMusicasResponse>").toString();
    }

    private String opObterMusica(Element req) {
        Musica m = service.obterMusica(childText(req, "id", ""));
        StringBuilder sb = new StringBuilder("<tns:ObterMusicaResponse>");
        appendMusica(sb, m);
        return sb.append("</tns:ObterMusicaResponse>").toString();
    }

    private String opCriarMusica(Element req) {
        Musica m = service.criarMusica(
                childText(req, "nome", ""),
                childText(req, "artista", ""),
                childText(req, "id", null)
        );
        StringBuilder sb = new StringBuilder("<tns:CriarMusicaResponse>");
        appendMusica(sb, m);
        return sb.append("</tns:CriarMusicaResponse>").toString();
    }

    private String opAtualizarMusica(Element req) {
        Musica m = service.atualizarMusica(
                childText(req, "id", ""),
                childText(req, "nome", ""),
                childText(req, "artista", "")
        );
        StringBuilder sb = new StringBuilder("<tns:AtualizarMusicaResponse>");
        appendMusica(sb, m);
        return sb.append("</tns:AtualizarMusicaResponse>").toString();
    }

    private String opRemoverMusica(Element req) {
        boolean ok = service.removerMusica(childText(req, "id", ""));
        return "<tns:RemoverMusicaResponse><tns:sucesso>" + ok + "</tns:sucesso></tns:RemoverMusicaResponse>";
    }

    private String opListarPlaylists(Element req) {
        StringBuilder sb = new StringBuilder("<tns:ListarPlaylistsResponse>");
        for (Playlist p : service.listarPlaylists()) {
            appendPlaylist(sb, p);
        }
        return sb.append("</tns:ListarPlaylistsResponse>").toString();
    }

    private String opObterPlaylist(Element req) {
        Playlist p = service.obterPlaylist(childText(req, "id", ""));
        StringBuilder sb = new StringBuilder("<tns:ObterPlaylistResponse>");
        appendPlaylist(sb, p);
        return sb.append("</tns:ObterPlaylistResponse>").toString();
    }

    private String opCriarPlaylist(Element req) {
        Playlist p = service.criarPlaylist(
                childText(req, "nome", ""),
                childText(req, "usuarioId", ""),
                childTexts(req, "musicaIds"),
                childText(req, "id", null)
        );
        StringBuilder sb = new StringBuilder("<tns:CriarPlaylistResponse>");
        appendPlaylist(sb, p);
        return sb.append("</tns:CriarPlaylistResponse>").toString();
    }

    private String opAtualizarPlaylist(Element req) {
        List<String> mids = hasChild(req, "musicaIds") ? childTexts(req, "musicaIds") : null;
        Playlist p = service.atualizarPlaylist(
                childText(req, "id", ""),
                childText(req, "nome", ""),
                childText(req, "usuarioId", null),
                mids
        );
        StringBuilder sb = new StringBuilder("<tns:AtualizarPlaylistResponse>");
        appendPlaylist(sb, p);
        return sb.append("</tns:AtualizarPlaylistResponse>").toString();
    }

    private String opRemoverPlaylist(Element req) {
        boolean ok = service.removerPlaylist(childText(req, "id", ""));
        return "<tns:RemoverPlaylistResponse><tns:sucesso>" + ok + "</tns:sucesso></tns:RemoverPlaylistResponse>";
    }

    private String opAdicionarMusicaNaPlaylist(Element req) {
        Playlist p = service.adicionarMusicaNaPlaylist(
                childText(req, "playlistId", ""),
                childText(req, "musicaId", "")
        );
        StringBuilder sb = new StringBuilder("<tns:AdicionarMusicaNaPlaylistResponse>");
        appendPlaylist(sb, p);
        return sb.append("</tns:AdicionarMusicaNaPlaylistResponse>").toString();
    }

    private String opRemoverMusicaDaPlaylist(Element req) {
        Playlist p = service.removerMusicaDaPlaylist(
                childText(req, "playlistId", ""),
                childText(req, "musicaId", "")
        );
        StringBuilder sb = new StringBuilder("<tns:RemoverMusicaDaPlaylistResponse>");
        appendPlaylist(sb, p);
        return sb.append("</tns:RemoverMusicaDaPlaylistResponse>").toString();
    }

    private String opListarPlaylistsPorUsuario(Element req) {
        StringBuilder sb = new StringBuilder("<tns:ListarPlaylistsPorUsuarioResponse>");
        for (Playlist p : service.listarPlaylistsPorUsuario(childText(req, "usuarioId", ""))) {
            appendPlaylist(sb, p);
        }
        return sb.append("</tns:ListarPlaylistsPorUsuarioResponse>").toString();
    }

    private String opListarMusicasPorPlaylist(Element req) {
        StringBuilder sb = new StringBuilder("<tns:ListarMusicasPorPlaylistResponse>");
        for (Musica m : service.listarMusicasPorPlaylist(childText(req, "playlistId", ""))) {
            appendMusica(sb, m);
        }
        return sb.append("</tns:ListarMusicasPorPlaylistResponse>").toString();
    }

    private String opListarPlaylistsPorMusica(Element req) {
        StringBuilder sb = new StringBuilder("<tns:ListarPlaylistsPorMusicaResponse>");
        for (Playlist p : service.listarPlaylistsPorMusica(childText(req, "musicaId", ""))) {
            appendPlaylist(sb, p);
        }
        return sb.append("</tns:ListarPlaylistsPorMusicaResponse>").toString();
    }

    private Path resolveSoapContractFile(String envVar, String filename) {
        List<Path> candidates = new ArrayList<>();
        String env = System.getenv(envVar);
        if (env != null && !env.isBlank()) {
            candidates.add(Path.of(env));
        }
        candidates.add(Path.of("contracts", "soap", filename));
        candidates.add(Path.of("..", "contracts", "soap", filename));
        return candidates.stream().filter(Files::isRegularFile).findFirst().orElse(null);
    }

    private static void appendUsuario(StringBuilder sb, Usuario u) {
        sb.append("<tns:usuario>")
                .append("<tns:id>").append(escapeXml(u.getId())).append("</tns:id>")
                .append("<tns:nome>").append(escapeXml(u.getNome())).append("</tns:nome>")
                .append("<tns:idade>").append(u.getIdade()).append("</tns:idade>")
                .append("</tns:usuario>");
    }

    private static void appendMusica(StringBuilder sb, Musica m) {
        sb.append("<tns:musica>")
                .append("<tns:id>").append(escapeXml(m.getId())).append("</tns:id>")
                .append("<tns:nome>").append(escapeXml(m.getNome())).append("</tns:nome>")
                .append("<tns:artista>").append(escapeXml(m.getArtista())).append("</tns:artista>")
                .append("</tns:musica>");
    }

    private static void appendPlaylist(StringBuilder sb, Playlist p) {
        sb.append("<tns:playlist>")
                .append("<tns:id>").append(escapeXml(p.getId())).append("</tns:id>")
                .append("<tns:nome>").append(escapeXml(p.getNome())).append("</tns:nome>")
                .append("<tns:usuarioId>").append(escapeXml(p.getUsuarioId())).append("</tns:usuarioId>");
        for (String mid : p.getMusicaIds()) {
            sb.append("<tns:musicaIds>").append(escapeXml(mid)).append("</tns:musicaIds>");
        }
        sb.append("</tns:playlist>");
    }

    private static String wrapEnvelope(String bodyContent) {
        return "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
                + "<soapenv:Envelope xmlns:soapenv=\"" + SOAP_ENV_NS + "\" xmlns:tns=\"" + TNS + "\">"
                + "<soapenv:Body>" + bodyContent + "</soapenv:Body></soapenv:Envelope>";
    }

    private static ResponseEntity<String> faultResponse(String code, String message, HttpStatus status) {
        String xml = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
                + "<soapenv:Envelope xmlns:soapenv=\"" + SOAP_ENV_NS + "\">"
                + "<soapenv:Body><soapenv:Fault>"
                + "<faultcode>" + escapeXml(code) + "</faultcode>"
                + "<faultstring>" + escapeXml(message) + "</faultstring>"
                + "</soapenv:Fault></soapenv:Body></soapenv:Envelope>";
        return ResponseEntity.status(status)
                .contentType(MediaType.parseMediaType("text/xml;charset=UTF-8"))
                .body(xml);
    }

    private static String localName(Node node) {
        return node.getLocalName() != null ? node.getLocalName() : node.getNodeName();
    }

    private static Element firstElementChild(Element parent) {
        NodeList children = parent.getChildNodes();
        for (int i = 0; i < children.getLength(); i++) {
            if (children.item(i) instanceof Element el) {
                return el;
            }
        }
        return null;
    }

    private static Element findFirstChildByLocalName(Element parent, String name) {
        NodeList children = parent.getChildNodes();
        for (int i = 0; i < children.getLength(); i++) {
            if (children.item(i) instanceof Element el && name.equals(localName(el))) {
                return el;
            }
        }
        return null;
    }

    private static boolean hasChild(Element parent, String name) {
        return findFirstChildByLocalName(parent, name) != null;
    }

    private static String childText(Element parent, String name, String defaultVal) {
        Element el = findFirstChildByLocalName(parent, name);
        return el != null ? el.getTextContent().trim() : defaultVal;
    }

    private static List<String> childTexts(Element parent, String name) {
        List<String> values = new ArrayList<>();
        NodeList children = parent.getChildNodes();
        for (int i = 0; i < children.getLength(); i++) {
            if (children.item(i) instanceof Element el && name.equals(localName(el))) {
                String txt = el.getTextContent().trim();
                if (!txt.isEmpty()) {
                    values.add(txt);
                }
            }
        }
        return values;
    }

    private static String escapeXml(String input) {
        if (input == null) {
            return "";
        }
        return input.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace("\"", "&quot;")
                .replace("'", "&apos;");
    }
}
