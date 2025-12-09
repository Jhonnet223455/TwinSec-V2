"""
RAG (Retrieval-Augmented Generation) Service

Sistema de recuperación de contexto desde libros técnicos para enriquecer
la generación de modelos con LLM.

Arquitectura:
1. Document Loader: Carga PDFs, DOCX, TXT
2. Text Splitter: Divide en chunks de 1000 caracteres
3. Embeddings: Convierte texto a vectores (sentence-transformers)
4. Vector Store: ChromaDB para búsqueda semántica
5. Retriever: Recupera top-k fragmentos relevantes
"""

import os
from pathlib import Path
from typing import List, Dict, Optional
import logging

# LangChain para RAG
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma
from langchain.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    TextLoader,
    DirectoryLoader
)
from langchain.schema import Document

logger = logging.getLogger(__name__)


class RAGService:
    """
    Servicio de Retrieval-Augmented Generation.
    
    Carga libros de sistemas dinámicos y permite búsqueda semántica
    para enriquecer prompts al LLM.
    """
    
    def __init__(
        self,
        knowledge_base_path: str = "knowledge_base",
        persist_directory: str = "chroma_db",
        embedding_model: str = "all-MiniLM-L6-v2"
    ):
        """
        Args:
            knowledge_base_path: Ruta a la carpeta con libros
            persist_directory: Dónde guardar el índice de ChromaDB
            embedding_model: Modelo de embeddings (HuggingFace)
        """
        self.knowledge_base_path = Path(knowledge_base_path)
        self.persist_directory = persist_directory
        
        # Inicializar embeddings (local, sin API)
        logger.info(f"Cargando modelo de embeddings: {embedding_model}")
        self.embeddings = HuggingFaceEmbeddings(
            model_name=embedding_model,
            model_kwargs={'device': 'cpu'},  # Cambiar a 'cuda' si tienes GPU
            encode_kwargs={'normalize_embeddings': True}
        )
        
        # Vector store (ChromaDB)
        self.vectorstore: Optional[Chroma] = None
        
        # Configuración de chunks
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,        # Tamaño del fragmento
            chunk_overlap=200,      # Overlap para mantener contexto
            length_function=len,
            separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""]
        )
        
        # Estadísticas
        self.stats = {
            "total_documents": 0,
            "total_chunks": 0,
            "indexed_files": []
        }
    
    def load_documents(self) -> List[Document]:
        """
        Carga todos los documentos de la carpeta knowledge_base.
        
        Soporta: PDF, DOCX, TXT
        Ignora: README.md y archivos de configuración
        """
        documents = []
        
        if not self.knowledge_base_path.exists():
            logger.warning(f"Knowledge base no encontrado: {self.knowledge_base_path}")
            self.knowledge_base_path.mkdir(parents=True, exist_ok=True)
            return documents
        
        logger.info(f"Cargando documentos desde: {self.knowledge_base_path}")
        
        # Archivos a ignorar
        ignore_files = {"README.md", "readme.md", ".gitkeep", ".gitignore"}
        
        try:
            # Cargar PDFs
            pdf_loader = DirectoryLoader(
                str(self.knowledge_base_path),
                glob="**/*.pdf",
                loader_cls=PyPDFLoader,
                show_progress=True
            )
            documents.extend(pdf_loader.load())
            logger.info(f"  📄 PDFs cargados: {len([d for d in documents if d.metadata.get('source', '').endswith('.pdf')])}")
        except Exception as e:
            logger.warning(f"Error cargando PDFs: {e}")
        
        try:
            # Cargar DOCX
            docx_loader = DirectoryLoader(
                str(self.knowledge_base_path),
                glob="**/*.docx",
                loader_cls=Docx2txtLoader,
                show_progress=True
            )
            docx_docs = docx_loader.load()
            documents.extend(docx_docs)
            logger.info(f"  📄 DOCX cargados: {len(docx_docs)}")
        except Exception as e:
            logger.warning(f"Error cargando DOCX: {e}")
        
        try:
            # Cargar TXT (excepto archivos ignorados)
            txt_files = list(self.knowledge_base_path.rglob("*.txt"))
            txt_files = [f for f in txt_files if f.name not in ignore_files]
            
            for txt_file in txt_files:
                try:
                    loader = TextLoader(str(txt_file))
                    documents.extend(loader.load())
                except Exception as e:
                    logger.warning(f"No se pudo cargar {txt_file.name}: {e}")
            
            logger.info(f"  📄 TXT cargados: {len(txt_files)}")
        except Exception as e:
            logger.warning(f"Error cargando TXT: {e}")
        
        # Filtrar documentos vacíos o README
        documents = [
            doc for doc in documents 
            if doc.page_content.strip() 
            and Path(doc.metadata.get("source", "")).name not in ignore_files
        ]
        
        logger.info(f"✅ Total documentos cargados: {len(documents)}")
        
        if len(documents) == 0:
            logger.warning("⚠️ No se encontraron documentos válidos en knowledge_base")
            logger.warning("💡 Agrega archivos PDF, DOCX o TXT con contenido técnico")
        
        # Actualizar estadísticas
        self.stats["total_documents"] = len(documents)
        self.stats["indexed_files"] = [doc.metadata.get("source", "unknown") for doc in documents]
        
        return documents
    
    def split_documents(self, documents: List[Document]) -> List[Document]:
        """
        Divide documentos en chunks más pequeños.
        """
        logger.info("Dividiendo documentos en chunks...")
        chunks = self.text_splitter.split_documents(documents)
        
        logger.info(f"✅ {len(chunks)} chunks creados")
        self.stats["total_chunks"] = len(chunks)
        
        return chunks
    
    def create_vectorstore(self, chunks: List[Document]) -> Chroma:
        """
        Crea el vector store con ChromaDB.
        """
        logger.info("Creando vector store con ChromaDB...")
        
        vectorstore = Chroma.from_documents(
            documents=chunks,
            embedding=self.embeddings,
            persist_directory=self.persist_directory
        )
        
        # Persistir en disco
        vectorstore.persist()
        
        logger.info(f"✅ Vector store creado y guardado en: {self.persist_directory}")
        
        return vectorstore
    
    def load_vectorstore(self) -> Optional[Chroma]:
        """
        Carga un vector store existente desde disco.
        """
        if not os.path.exists(self.persist_directory):
            logger.warning(f"Vector store no encontrado en: {self.persist_directory}")
            return None
        
        logger.info(f"Cargando vector store desde: {self.persist_directory}")
        
        vectorstore = Chroma(
            persist_directory=self.persist_directory,
            embedding_function=self.embeddings
        )
        
        logger.info("✅ Vector store cargado")
        
        return vectorstore
    
    def initialize(self, force_reindex: bool = False):
        """
        Inicializa el sistema RAG.
        
        Args:
            force_reindex: Si True, re-indexa aunque exista el vector store
        """
        # Intentar cargar vector store existente
        if not force_reindex:
            self.vectorstore = self.load_vectorstore()
            
            if self.vectorstore is not None:
                logger.info("📚 Sistema RAG listo (usando índice existente)")
                return
        
        # Si no existe o force_reindex, crear nuevo
        logger.info("📚 Inicializando sistema RAG (primera vez o re-indexación)...")
        
        # 1. Cargar documentos
        documents = self.load_documents()
        
        if not documents:
            logger.warning("⚠️ No se encontraron documentos en knowledge_base")
            logger.warning("Copia libros en formato PDF/DOCX/TXT a la carpeta knowledge_base/")
            return
        
        # 2. Dividir en chunks
        chunks = self.split_documents(documents)
        
        # 3. Crear vector store
        self.vectorstore = self.create_vectorstore(chunks)
        
        logger.info("✅ Sistema RAG inicializado correctamente")
    
    def retrieve_context(
        self,
        query: str,
        top_k: int = 5,
        min_relevance_score: float = 0.5
    ) -> List[Dict]:
        """
        Recupera fragmentos relevantes del knowledge base.
        
        Args:
            query: Consulta del usuario
            top_k: Número de fragmentos a recuperar
            min_relevance_score: Score mínimo de relevancia (0-1)
        
        Returns:
            Lista de fragmentos con metadata:
            [
                {
                    "content": "texto del fragmento...",
                    "source": "path/to/book.pdf",
                    "page": 145,
                    "score": 0.85
                }
            ]
        """
        if self.vectorstore is None:
            logger.warning("Vector store no inicializado")
            return []
        
        # Búsqueda semántica con scores
        results = self.vectorstore.similarity_search_with_score(
            query,
            k=top_k
        )
        
        # Filtrar por relevancia
        relevant_results = [
            {
                "content": doc.page_content,
                "source": doc.metadata.get("source", "unknown"),
                "page": doc.metadata.get("page", None),
                "score": float(1 - score)  # ChromaDB usa distancia, invertir a similitud
            }
            for doc, score in results
            if (1 - score) >= min_relevance_score
        ]
        
        logger.info(f"📖 Recuperados {len(relevant_results)}/{top_k} fragmentos relevantes")
        
        return relevant_results
    
    def format_context_for_prompt(self, context_results: List[Dict]) -> str:
        """
        Formatea el contexto recuperado para incluirlo en el prompt.
        
        Args:
            context_results: Resultados de retrieve_context()
        
        Returns:
            String formateado para agregar al prompt
        """
        if not context_results:
            return ""
        
        formatted = "TECHNICAL CONTEXT FROM KNOWLEDGE BASE:\n\n"
        
        for i, result in enumerate(context_results, 1):
            source = Path(result["source"]).name
            page = f", page {result['page']}" if result["page"] else ""
            score = result["score"]
            
            formatted += f"[Reference {i}] (Source: {source}{page}, Relevance: {score:.2f})\n"
            formatted += f"{result['content']}\n\n"
        
        formatted += "---\n\n"
        formatted += "Use the above technical context to inform your model generation.\n"
        formatted += "Cite specific equations, parameters, and design patterns from the references.\n\n"
        
        return formatted
    
    def get_stats(self) -> Dict:
        """
        Retorna estadísticas del sistema RAG.
        """
        return {
            **self.stats,
            "vectorstore_initialized": self.vectorstore is not None,
            "embedding_model": self.embeddings.model_name
        }


# Singleton global
_rag_service: Optional[RAGService] = None


def get_rag_service() -> RAGService:
    """
    Obtiene la instancia singleton del RAG service.
    """
    global _rag_service
    
    if _rag_service is None:
        from app.config import get_settings
        settings = get_settings()
        
        # Ruta al knowledge base (relativa al proyecto)
        knowledge_base_path = Path(__file__).parent.parent.parent.parent / "knowledge_base"
        chroma_db_path = Path(__file__).parent.parent.parent / "chroma_db"
        
        _rag_service = RAGService(
            knowledge_base_path=str(knowledge_base_path),
            persist_directory=str(chroma_db_path)
        )
        
        # Inicializar (cargar o crear índice)
        _rag_service.initialize()
    
    return _rag_service
