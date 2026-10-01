import asyncio
import aiohttp
import aiofiles
import os
import urllib.parse
import re

class UnpaywallDownloader:
    def __init__(self):
        self.email = ""
        self.api_base = "https://api.unpaywall.org/v2/"
        self.cancel_event = asyncio.Event()

    async def _get_with_retry(self, session, url, retries=3, as_json=True):
        import random
        for attempt in range(retries):
            if self.cancel_event.is_set():
                return None
            try:
                async with session.get(url, timeout=15) as response:
                    if response.status == 200:
                        return await response.json() if as_json else await response.text()
                    elif response.status in (429, 500, 502, 503, 504):
                        # Smart Jittered Backoff to prevent thundering herd
                        jitter = random.uniform(0.5, 1.5)
                        await asyncio.sleep((2 ** attempt) + jitter)
                        continue
                    else:
                        return None
            except Exception as e:
                if attempt == retries - 1:
                    print(f"Request failed after {retries} attempts for {url}: {e}")
                else:
                    await asyncio.sleep(2 ** attempt)
        return None
        
    async def fetch_pdf_url(self, session, doi):
        if self.cancel_event.is_set(): return None
        
        # 1. Try Unpaywall
        url = f"{self.api_base}{doi}?email={self.email}"
        data = await self._get_with_retry(session, url)
        if data:
            best_oa_location = data.get('best_oa_location')
            if best_oa_location and best_oa_location.get('url_for_pdf'):
                return best_oa_location.get('url_for_pdf')
            
        # 2. Fallback to Crossref
        crossref_url = f"https://api.crossref.org/works/{doi}"
        data = await self._get_with_retry(session, crossref_url)
        if data:
            links = data.get('message', {}).get('link', [])
            for link in links:
                if link.get('content-type') == 'application/pdf':
                    return link.get('URL')

        # 3. Fallback to Europe PMC
        epmc_url = f"https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:{doi}&resultType=core&format=json"
        data = await self._get_with_retry(session, epmc_url)
        if data:
            results = data.get('resultList', {}).get('result', [])
            if results:
                ft_links = results[0].get('fullTextUrlList', {}).get('fullTextUrl', [])
                for ft in ft_links:
                    if ft.get('documentStyle') == 'pdf':
                        return ft.get('url')
            
        # 4. Fallback to OpenAlex
        openalex_url = f"https://api.openalex.org/works/https://doi.org/{doi}"
        data = await self._get_with_retry(session, openalex_url)
        if data:
            oa_info = data.get('open_access', {})
            if oa_info.get('is_oa') and oa_info.get('oa_url'):
                return oa_info.get('oa_url')

        # 5. Fallback to Semantic Scholar
        semanticscholar_url = f"https://api.semanticscholar.org/graph/v1/paper/DOI:{doi}?fields=openAccessPdf"
        data = await self._get_with_retry(session, semanticscholar_url)
        if data:
            oa_pdf = data.get('openAccessPdf', {})
            if oa_pdf and oa_pdf.get('url'):
                return oa_pdf.get('url')
                
        # 6. Fallback to Internet Archive Scholar (Fatcat)
        fatcat_url = f"https://api.fatcat.wiki/v0/release/lookup?doi={doi}"
        data = await self._get_with_retry(session, fatcat_url)
        if data and data.get('files'):
            for file_meta in data.get('files', []):
                if file_meta.get('mimetype') == 'application/pdf':
                    urls = file_meta.get('urls', [])
                    for url_obj in urls:
                        if url_obj.get('url'): return url_obj.get('url')
                        
        # 7. Fallback to HAL (French National Archive)
        hal_url = f"https://api.archives-ouvertes.fr/search/?q=doiId_s:\"{doi}\"&fl=fileMain_s&wt=json"
        data = await self._get_with_retry(session, hal_url)
        if data:
            docs = data.get('response', {}).get('docs', [])
            if docs and docs[0].get('fileMain_s'):
                return docs[0].get('fileMain_s')
                
        # 8. Fallback to Zenodo Open Science Repository
        zenodo_url = f"https://zenodo.org/api/records?q=doi:\"{doi}\""
        data = await self._get_with_retry(session, zenodo_url)
        if data:
            hits = data.get('hits', {}).get('hits', [])
            if hits:
                files = hits[0].get('files', [])
                if files:
                    links = files[0].get('links', {})
                    if links.get('self'): return links.get('self')
                    
        # 9. Fallback to arXiv (Physics, Math, CS preprints)
        arxiv_url = f"http://export.arxiv.org/api/query?search_query=doi:{doi}"
        text_data = await self._get_with_retry(session, arxiv_url, as_json=False)
        if text_data and "<link title=\"pdf\"" in text_data:
            match = re.search(r'<link title="pdf"\s+href="([^"]+)"', text_data)
            if match:
                return match.group(1) + ".pdf"

        # 10. Fallback to bioRxiv (Biology preprints)
        biorxiv_url = f"https://api.biorxiv.org/details/biorxiv/{doi}"
        data = await self._get_with_retry(session, biorxiv_url)
        if data and isinstance(data, dict):
            msgs = data.get("messages", [])
            if msgs and msgs[0].get("status") == "ok":
                collection = data.get("collection", [])
                if collection:
                    return f"https://www.biorxiv.org/content/{doi}v{collection[-1].get('version')}.full.pdf"

        # 11. Fallback to medRxiv (Medical preprints)
        medrxiv_url = f"https://api.biorxiv.org/details/medrxiv/{doi}"
        data = await self._get_with_retry(session, medrxiv_url)
        if data and isinstance(data, dict):
            msgs = data.get("messages", [])
            if msgs and msgs[0].get("status") == "ok":
                collection = data.get("collection", [])
                if collection:
                    return f"https://www.medrxiv.org/content/{doi}v{collection[-1].get('version')}.full.pdf"
        # 12. Fallback to PubMed Central (US) Direct API
        pmc_search = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pmc&term={doi}[doi]&retmode=json"
        pmc_data = await self._get_with_retry(session, pmc_search)
        if pmc_data and isinstance(pmc_data, dict):
            idlist = pmc_data.get("esearchresult", {}).get("idlist", [])
            if idlist:
                return f"https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{idlist[0]}/pdf/"

        # 13. Fallback to DOAJ (Directory of Open Access Journals)
        doaj_url = f"https://doaj.org/api/v1/search/articles/doi:{doi}"
        doaj_data = await self._get_with_retry(session, doaj_url)
        if doaj_data and isinstance(doaj_data, dict):
            results = doaj_data.get("results", [])
            if results:
                link = results[0].get("bibjson", {}).get("link", [])
                for l in link:
                    if l.get("type") == "fulltext" and l.get("url", "").endswith(".pdf"):
                        return l.get("url")

        # 14. Fallback to OpenAIRE
        openaire_url = f"https://api.openaire.eu/search/publications?doi={doi}&format=json"
        oa_data = await self._get_with_retry(session, openaire_url, as_json=False)
        if oa_data:
            match = re.search(r'(https?://[^\s"\'\{\}]+\.pdf)', oa_data)
            if match:
                return match.group(1)
            
        return None

    async def fetch_pdf_url_by_title(self, session, title):
        if not title or len(title) < 5 or self.cancel_event.is_set(): return None
        encoded_title = urllib.parse.quote(title)
        
        # 1. Semantic Scholar Title Search
        ss_url = f"https://api.semanticscholar.org/graph/v1/paper/search?query={encoded_title}&fields=openAccessPdf,externalIds&limit=3"
        data = await self._get_with_retry(session, ss_url)
        if data and isinstance(data, dict):
            for paper in data.get('data', []):
                oa = paper.get('openAccessPdf')
                if oa and oa.get('url'):
                    return oa.get('url')
                ext_ids = paper.get('externalIds', {})
                if ext_ids and ext_ids.get('DOI'):
                    pdf = await self.fetch_pdf_url(session, ext_ids.get('DOI'))
                    if pdf: return pdf

        # 2. Crossref Title Search
        cr_url = f"https://api.crossref.org/works?query.title={encoded_title}&select=DOI,link,title&rows=3"
        data = await self._get_with_retry(session, cr_url)
        if data and isinstance(data, dict):
            items = data.get('message', {}).get('items', [])
            for item in items:
                item_title = item.get('title', [''])[0].lower()
                # Basic sanity check
                if len(item_title) > 5 and item_title[:10] in title.lower():
                    links = item.get('link', [])
                    for link in links:
                        if link.get('content-type') == 'application/pdf':
                            return link.get('URL')
                    if item.get('DOI'):
                        pdf = await self.fetch_pdf_url(session, item.get('DOI'))
                        if pdf: return pdf
                        
        return None

    def sanitize_filename(self, title):
        clean = re.sub(r'[\\/*?:"<>|]', "", title)
        return clean[:150] + ".pdf"

    async def download_pdf(self, session, pdf_url, title, out_dir):
        if not pdf_url:
            return False
            
        filename = self.sanitize_filename(title)
        filepath = os.path.join(out_dir, filename)
        part_filepath = filepath + ".part"
        
        for attempt in range(3):
            if self.cancel_event.is_set():
                break
            try:
                async with session.get(pdf_url, timeout=30) as response:
                    if response.status == 200:
                        content_type = response.headers.get('Content-Type', '').lower()
                        if 'application/pdf' not in content_type:
                            return False
                            
                        # Async/Atomic write to .part file using aiofiles
                        async with aiofiles.open(part_filepath, 'wb') as f:
                            async for chunk in response.content.iter_chunked(1024 * 64):
                                if self.cancel_event.is_set():
                                    break
                                await f.write(chunk)
                                
                        if self.cancel_event.is_set():
                            if os.path.exists(part_filepath): os.remove(part_filepath)
                            return False
                            
                        # Rename upon success
                        if os.path.exists(filepath):
                            os.remove(filepath)
                        os.rename(part_filepath, filepath)
                        return True
                    elif response.status in (429, 500, 502, 503, 504):
                        await asyncio.sleep(2 ** attempt)
                        continue
                    else:
                        break # Unrecoverable status
            except Exception as e:
                await asyncio.sleep(2 ** attempt)
                
        if os.path.exists(part_filepath):
            os.remove(part_filepath)
        return False

    async def process_reference(self, session, ref, out_dir, callback=None):
        if self.cancel_event.is_set():
            return

        doi = ref.get("doi")
        title = ref.get("title", "")
        
        # Check if file already exists in the destination folder
        filename = self.sanitize_filename(title if title else (doi if doi else "Unknown Title"))
        filepath = os.path.join(out_dir, filename)
        if os.path.exists(filepath):
            ref["status"] = "Downloaded"
            if callback: callback(ref)
            return
            
        await asyncio.sleep(0.1)
        
        pdf_url = None
        if doi:
            pdf_url = await self.fetch_pdf_url(session, doi)
            
        # Title search fallback
        if not pdf_url and title and len(title) > 5 and "Extracted Document" not in title:
            pdf_url = await self.fetch_pdf_url_by_title(session, title)
            
        if pdf_url:
            success = await self.download_pdf(session, pdf_url, title if title else (doi if doi else "Unknown Title"), out_dir)
            if self.cancel_event.is_set(): return
            ref["status"] = "Downloaded" if success else "Failed to Download"
        else:
            if self.cancel_event.is_set(): return
            ref["status"] = "Manual Access Required"
        
        if callback: callback(ref)
            
    async def batch_download(self, references, out_dir, callback=None):
        self.cancel_event.clear()
        
        # High-Performance Connection Pooling (15 concurrent connections per API domain, 60 overall)
        connector = aiohttp.TCPConnector(limit_per_host=15, limit=60)
        
        # Open Access "Polite Pool" standard User-Agent (crucial for Crossref, Unpaywall, OpenAlex APIs)
        headers = {
            'User-Agent': 'MultiReferenceDownloader/1.1.0 (mailto:researcher@openscience.org) aiohttp/3.9.3'
        }
        
        # Concurrency limit to prevent memory/loop flooding
        sem = asyncio.Semaphore(50)
        
        async def bounded_process(session, ref):
            async with sem:
                await self.process_reference(session, ref, out_dir, callback)
                
        async with aiohttp.ClientSession(connector=connector, headers=headers) as session:
            tasks = []
            for ref in references:
                if ref["status"] == "Pending":
                    tasks.append(bounded_process(session, ref))
                    
            await asyncio.gather(*tasks)
