import './index.css';
import { useEffect, useState, useMemo } from 'react';
import { supabase } from './lib/supabase';
import Navbar from './components/Navbar';
import MovieRow from './components/MovieRow';
import MovieModal from './components/MovieModal';
import { Filter, SortAsc, SortDesc, Calendar, Search, LayoutGrid, Layers } from 'lucide-react';

function App() {
  const [movies, setMovies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedMovie, setSelectedMovie] = useState(null);
  const [panelRowKey, setPanelRowKey] = useState(null);
  
  // Search and Filter State
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState('newest'); 
  const [filterGenre, setFilterGenre] = useState('All');
  const [filterYear, setFilterYear] = useState('All Years');
  const [activeCategory, setActiveCategory] = useState('Home');

  useEffect(() => {
    fetchMovies();
  }, []);

  const fetchMovies = async () => {
    try {
      const { data, error } = await supabase
        .from('tamil_movies')
        .select('*')
        .order('id', { ascending: false });

      if (error) {
        console.error('Error fetching movies:', error);
      } else {
        setMovies(data || []);
      }
    } catch (err) {
      console.error('Exception fetching movies:', err);
    } finally {
      setLoading(false);
    }
  };

  // Extract metadata for dropdowns
  const { allGenres, allYears } = useMemo(() => {
    const genresSet = new Set(['All']);
    const yearsSet = new Set(['All Years']);
    
    movies.forEach(m => {
      // Genres
      const gStr = m.gentre || m.genre;
      if (gStr) {
        gStr.split(',').forEach(g => genresSet.add(g.trim()));
      }
      // Years
      const y = m.release_year || m.year;
      if (y && !isNaN(y)) yearsSet.add(y.toString());
    });

    return {
      allGenres: [...genresSet].sort(),
      allYears: [...yearsSet].sort((a, b) => b - a)
    };
  }, [movies]);

  // Derived filtered and sorted movies
  const filteredMovies = useMemo(() => {
    let result = [...movies];

    // 1. Navbar Category Filter
    if (activeCategory === 'Movies') {
      result = result.filter(m => {
        const g = (m.gentre || m.genre || '').toLowerCase();
        return !g.includes('tv') && !g.includes('series');
      });
    } else if (activeCategory === 'TV Shows') {
      result = result.filter(m => {
        const g = (m.gentre || m.genre || '').toLowerCase();
        return g.includes('tv') || g.includes('series');
      });
    }

    // 2. Search Filter
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      result = result.filter(m => 
        m.movie_name.toLowerCase().includes(q) || 
        (m.stars && m.stars.toLowerCase().includes(q)) ||
        (m.director_name && m.director_name.toLowerCase().includes(q)) ||
        (m.gentre || m.genre || '').toLowerCase().includes(q)
      );
    }

    // 3. Genre Filter
    if (filterGenre !== 'All') {
      result = result.filter(m => (m.gentre || m.genre || '').includes(filterGenre));
    }

    // 4. Year Filter
    if (filterYear !== 'All Years') {
      result = result.filter(m => (m.release_year || m.year || '').toString() === filterYear);
    }

    // 5. Sorting
    result.sort((a, b) => {
      if (sortBy === 'newest') {
        return (b.release_year || b.year || 0) - (a.release_year || a.year || 0);
      }
      if (sortBy === 'oldest') {
        const yA = a.release_year || a.year || 9999;
        const yB = b.release_year || b.year || 9999;
        return yA - yB;
      }
      if (sortBy === 'alphabetical') {
        return a.movie_name.localeCompare(b.movie_name);
      }
      return 0;
    });

    return result;
  }, [movies, searchQuery, sortBy, filterGenre, filterYear, activeCategory]);

  const displayGenres = useMemo(() => {
    const rawGenres = filteredMovies.map(m => m.gentre || m.genre).filter(Boolean);
    const splitGenres = rawGenres.flatMap(g => g.split(',').map(s => s.trim()));
    const counts = {};
    splitGenres.forEach(g => counts[g] = (counts[g] || 0) + 1);
    return Object.keys(counts).sort((a, b) => counts[b] - counts[a]).slice(0, 6);
  }, [filteredMovies]);

  const heroMovie = movies.length > 0 ? (selectedMovie || movies[0]) : null;

  const handleMovieClick = (movie, rowKey) => {
    setSelectedMovie(movie);
    setPanelRowKey(rowKey);
    // Scroll to top to see movie details or use the modal
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const closePanel = () => { setSelectedMovie(null); setPanelRowKey(null); };

  const rows = useMemo(() => {
    const r = [];
    if (filteredMovies.length === 0) return r;

    if (searchQuery || filterGenre !== 'All' || filterYear !== 'All Years' || activeCategory !== 'Home') {
      r.push({ key: 'filtered-results', title: activeCategory !== 'Home' ? activeCategory : 'Found for you', movies: filteredMovies });
      return r;
    }

    r.push({ key: 'recent', title: 'Recently Added', movies: filteredMovies.slice(0, 15) });
    displayGenres.forEach((genre, idx) => {
      const rowMovies = filteredMovies.filter(m => (m.gentre || m.genre || '').includes(genre));
      if (rowMovies.length > 0) {
        r.push({ key: genre, title: `${genre} Collection`, movies: rowMovies, index: idx + 1 });
      }
    });

    return r;
  }, [filteredMovies, searchQuery, filterGenre, filterYear, activeCategory, displayGenres]);

  const handleCategoryChange = (cat) => {
    setActiveCategory(cat);
    setSearchQuery('');
    setFilterGenre('All');
    setFilterYear('All Years');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <div className="min-h-screen bg-[#090910] font-sans text-[#f2efe8] selection:bg-[#e8192c]/30">
      <Navbar 
        onSearch={setSearchQuery} 
        searchQuery={searchQuery} 
        activeCategory={activeCategory}
        onCategoryChange={handleCategoryChange}
      />

      {loading ? (
        <div className="flex flex-col items-center justify-center h-screen bg-[#090910]">
          <div className="relative">
             <div className="w-20 h-20 border-2 border-[#e8192c]/20 border-t-[#e8192c] rounded-full animate-spin shadow-[0_0_40px_rgba(232,25,44,0.15)]" />
             <div className="absolute inset-0 flex items-center justify-center">
                <div className="w-1.5 h-1.5 bg-[#e8192c] rounded-full animate-pulse" />
             </div>
          </div>
          <p className="mt-8 text-[#7a7a8c] font-bold tracking-[0.4em] uppercase text-[10px] animate-pulse">Loading Universe</p>
        </div>
      ) : (
        <div className="animate-in fade-in duration-700">
          <main className="relative pt-28">

          {/* Premium Sub-Nav */}
          <div className="sticky top-[72px] z-40 px-4 md:px-11 py-4 flex flex-wrap items-center justify-between gap-4 border-b border-white/5 bg-[#090910]/80 backdrop-blur-xl transition-all">
             <div className="flex items-center gap-3">
                <div className="w-1 h-5 bg-[#e8192c] rounded-full" />
                <h2 className="font-['Bebas_Neue'] text-2xl tracking-[1.5px] text-[#f2efe8] uppercase">
                  {searchQuery ? `Search: ${searchQuery}` : activeCategory}
                </h2>
                {filteredMovies.length > 0 && (
                  <span className="bg-white/5 text-[#7a7a8c] text-[10px] px-2.5 py-0.5 rounded-full font-bold ml-1 border border-white/5">
                    {filteredMovies.length}
                  </span>
                )}
             </div>

             <div className="flex items-center gap-3 overflow-x-auto no-scrollbar scroll-smooth">
                {/* Year Selection */}
                <div className="flex items-center gap-2 bg-white/5 border border-white/10 px-3 py-1.5 rounded-lg hover:bg-white/10 transition group">
                  <Calendar className="w-3.5 h-3.5 text-[#e8192c]" />
                  <select 
                    className="bg-transparent text-[11px] font-bold outline-none cursor-pointer text-[#7a7a8c] group-hover:text-[#f2efe8] transition min-w-[80px]"
                    value={filterYear}
                    onChange={(e) => setFilterYear(e.target.value)}
                  >
                    <option value="All Years" className="bg-[#111118]">All Years</option>
                    {allYears.filter(y => y !== 'All Years').map(y => <option key={y} value={y} className="bg-[#111118]">{y}</option>)}
                  </select>
                </div>

                {/* Genre Selection */}
                <div className="flex items-center gap-2 bg-white/5 border border-white/10 px-3 py-1.5 rounded-lg hover:bg-white/10 transition group">
                  <LayoutGrid className="w-3.5 h-3.5 text-[#f5c842]" />
                  <select 
                    className="bg-transparent text-[11px] font-bold outline-none cursor-pointer text-[#7a7a8c] group-hover:text-[#f2efe8] transition min-w-[80px]"
                    value={filterGenre}
                    onChange={(e) => setFilterGenre(e.target.value)}
                  >
                    {allGenres.map(g => <option key={g} value={g} className="bg-[#111118]">{g}</option>)}
                  </select>
                </div>

                {/* Sort Order */}
                <div className="flex items-center gap-2 bg-white/5 border border-white/10 px-3 py-1.5 rounded-lg hover:bg-white/10 transition group">
                  <Layers className="w-3.5 h-3.5 text-[#e8192c]" />
                  <select 
                    className="bg-transparent text-[11px] font-bold outline-none cursor-pointer text-[#7a7a8c] group-hover:text-[#f2efe8] transition min-w-[100px]"
                    value={sortBy}
                    onChange={(e) => setSortBy(e.target.value)}
                  >
                    <option value="newest" className="bg-[#111118]">Newest First</option>
                    <option value="oldest" className="bg-[#111118]">Oldest First</option>
                    <option value="alphabetical" className="bg-[#111118]">Alphabetical</option>
                  </select>
                </div>
             </div>
          </div>

          <div className="relative z-20 space-y-4 pb-24 px-4 md:px-11 min-h-[60vh]">
            {rows.length > 0 ? (
              rows.map((row) => (
                <div key={row.key}>
                  <MovieRow
                    title={row.title}
                    movies={row.movies}
                    onMovieClick={(movie) => handleMovieClick(movie, row.key)}
                  />
                </div>
              ))
            ) : (
              <div className="flex flex-col items-center justify-center py-40 text-[#7a7a8c]">
                <div className="relative mb-8">
                   <Search className="w-20 h-20 opacity-5" />
                   <div className="absolute inset-x-0 bottom-0 h-[1px] bg-gradient-to-r from-transparent via-[#e8192c] to-transparent" />
                </div>
                <p className="text-xl font-['Bebas_Neue'] tracking-[3px] text-[#f2efe8] uppercase mb-2">No Titles Found</p>
                <p className="text-xs text-[#7a7a8c] uppercase tracking-widest text-center px-10">Try adjusting your premium filters or search terms.</p>
                <button 
                  onClick={() => {setSearchQuery(''); setFilterGenre('All'); setFilterYear('All Years'); setActiveCategory('Home');}}
                  className="mt-10 px-8 py-3 bg-white/5 border border-white/10 hover:bg-white/10 text-[#f2efe8] text-[10px] font-bold rounded-xl transition-all uppercase tracking-[3px]"
                >
                  Reset Library
                </button>
              </div>
            )}
          </div>
        </main>

        {/* Selected Movie Modal */}
        {selectedMovie && (
          <MovieModal 
            movie={selectedMovie} 
            allMovies={movies} 
            onMovieClick={setSelectedMovie}
            onClose={closePanel} 
          />
        )}
      </div>
    )}

      {/* Premium Footer */}
      <footer className="w-full bg-[#090910] py-20 border-t border-white/5 flex flex-col items-center gap-8">
        <div className="font-['Bebas_Neue'] text-2xl tracking-[6px] text-[#e8192c] opacity-50">
          KOLL<span className="text-[#f5c842]">Y</span>WOOD
        </div>
        <div className="flex gap-10 text-[10px] font-bold text-[#7a7a8c] uppercase tracking-[3px]">
           <span className="hover:text-[#f2efe8] cursor-pointer transition">Terms</span>
           <span className="hover:text-[#f2efe8] cursor-pointer transition">Privacy</span>
           <span className="hover:text-[#f2efe8] cursor-pointer transition">Legal</span>
        </div>
        <p className="text-[#3a3a4a] text-[10px] tracking-[4px] font-bold uppercase flex items-center gap-4">
          © 2026 KOLLYWOOD PREMIUM EXPERIENCE
          <span className="w-1 h-1 bg-[#e8192c] rounded-full" />
          <span className="font-['Noto_Sans_Tamil'] tracking-normal text-[#e8192c] font-normal">கோலிவுட்</span>
        </p>
      </footer>
    </div>
  );
}

export default App;
